data "aws_vpc" "vpc" {
  id = var.vpc_id
}

locals {
  security_group_name = substr( "sgrp-${var.tags.Environment}${var.tags.Zone}${var.tags.Tier}-${var.name}-alb", 0, 255)
}

resource "aws_security_group" "for_alb" {
  #checkov:skip=CKV2_AWS_5:Checkov does not support the use of count
  #checkov:skip=CKV_AWS_260:Security Group for ALB, ALB will redirect port 80 to port 443
  count       = var.security_group_ids == null ? 1 : 0
  name        = local.security_group_name
  description = "Security group for the ALB."
  vpc_id      = var.vpc_id

    tags = merge({
    Name = local.security_group_name
  }, local.tags, var.additional_tags)

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = var.security_group_ingress_cidr_blocks == null ? [data.aws_vpc.vpc.cidr_block] : var.security_group_ingress_cidr_blocks
    description = "Ingress rule that allows port 80 from anywhere"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound connections"
  }

  lifecycle {
    # Necessary if changing 'name' or 'name_prefix' properties.
    create_before_destroy = true
  }
}

module "access_logs_s3_bucket" {
  # source = "sgts.gitlab-dedicated.com/wog/svc-iac-layer-1-simple-s3-private-bucket/aws"
  # version = "~>2.0"
  source  = "../s3"
  count   = var.access_logs == null ? 1 : 0 # create S3 bucket only if access logs are not provided

  bucket = "${data.aws_caller_identity.current.account_id}-elb-access-logs"
  versioning = var.versioning
  force_destroy = var.force_destroy
  bucket_key_enabled = var.bucket_key_enabled
  aws_s3_bucket_logging = var.aws_s3_bucket_logging
  bucket_policy = data.aws_iam_policy_document.aws_log_delivery_write
  tags = var.tags
  additional_tags = var.additional_tags
}

locals {
  bucket_name = var.access_logs == null ? module.access_logs_s3_bucket[0].bucket.id : var.access_logs.bucket
  # prefix      = var.access_logs == null ? var.name : var.access_logs.prefix
}

data "aws_iam_policy_document" "aws_log_delivery_write" {
  # https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-access-logs.html#access-logging-bucket-requirements
  # Allow AWS account to put files
  statement {
    sid = "albAWSLogDeliveryWrite"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.elb-account-id}:root"]
    }
    actions = [
      "s3:PutObject"
    ]
    resources = [
      "arn:aws:s3:::${local.bucket_name}",
      "arn:aws:s3:::${local.bucket_name}/*"
    ]
  }

  statement {
    sid = "nlbAWSLogDeliveryAclCheck"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }
    actions = [
      "s3:GetBucketAcl"
    ]
    resources = [
      "arn:aws:s3:::${local.bucket_name}",
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values = [
        "${data.aws_caller_identity.current.account_id}",
      ]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values = [
        "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*",
      ]
    }
  }

  statement {
    sid = "nlbAWSLogDeliveryWrite"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }
    actions = [
      "s3:PutObject"
    ]
    resources = [
      "arn:aws:s3:::${local.bucket_name}/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values = [
        "${data.aws_caller_identity.current.account_id}",
      ]
    }

    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values = [
        "bucket-owner-full-control",
      ]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values = [
        "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*",
      ]
    }
  }
}

# resource "aws_s3_bucket_policy" "aws_log_delivery_write" {
#   count  = var.access_logs == null ? 1 : 0
#   bucket = module.access_logs_s3_bucket[0].bucket.id
#   policy = data.aws_iam_policy_document.aws_log_delivery_write[0].json
# }

locals {
  # access_logs = var.access_logs == null ? {
  #   bucket = module.access_logs_s3_bucket[0].bucket.id
  #   prefix = var.name
  # } : var.access_logs


  lb_prefix   = var.load_balancer_type == "application" ? local.alb_prefix : local.nlb_prefix
  lb_name     = substr("${local.lb_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}-${var.name}", 0, 32)
  # lb_name     = var.load_balancer_type == "application" ? substr("${local.alb_name}-${var.name}", 0, 32) : "nlb" 
}

resource "aws_lb" "simple_lb" {
  #checkov:skip=CKV2_AWS_20:This is an internal load balancer, not exposed to the internet, expected traffic is HTTP
  #checkov:skip=CKV_AWS_150:Deletion protection MUST be enabled to support clean up jobs

  name                       = local.lb_name
  internal                   = var.internal
  load_balancer_type         = var.load_balancer_type
  subnets                    = length( var.subnet_mapping ) == 0 ? var.subnet_ids : null
  enable_deletion_protection = var.enable_deletion_protection
  security_groups            = var.security_group_ids == null ? [aws_security_group.for_alb[0].id] : var.security_group_ids
  drop_invalid_header_fields = true #This is to satisfy checkov CKV_AWS_131
  idle_timeout               = var.load_balancer_type == "application" ?  var.idle_timeout : null

  access_logs {
    bucket  = var.access_logs == null ? module.access_logs_s3_bucket[0].bucket.id : var.access_logs.bucket
    # prefix  = var.access_logs == null ? var.name : var.access_logs.prefix
    prefix  = local.lb_name
    enabled = true
  }

  dynamic "subnet_mapping" {
    for_each = var.subnet_mapping

    content {
      subnet_id     = var.subnet_ids[ index(var.subnet_mapping, subnet_mapping.value) ]
      allocation_id = subnet_mapping.value
    }
  }

  tags = merge(
    {
      "Name" = local.lb_name
      "type" = local.lb_prefix
      "scheme" = var.internal ? "private" : "public"
    },
    local.tags,
    var.additional_tags
  )

  # checkov:skip=CKV2_AWS_20: "Redirection from HTTP to HTTPS can be skipped for ALB"
}

resource "aws_lb_listener" "alb_listener_port_80" {
  count = var.load_balancer_type == "application" ? 1: 0
  #Disable checkov aws2 as this is an  "internal" load balancer
  #checkov:skip=CKV_AWS_2:This is an internal load balancer, not exposed to the internet
  #checkov:skip=CKV_AWS_103:This is an internal load balancer, not exposed to the internet

  load_balancer_arn = aws_lb.simple_lb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    order = 1
    type  = "redirect"

    redirect {
      host        = "#{host}"
      path        = "/#{path}"
      port        = "443"
      protocol    = "HTTPS"
      query       = "#{query}"
      status_code = "HTTP_301"
    }
  }

  tags = merge(
    {
      "type" = aws_lb.simple_lb.load_balancer_type == "application" ?  local.alb_prefix: local.nlb_prefix
      "scheme" = aws_lb.simple_lb.internal ? "private" : "public"
    },
    local.tags,
    var.additional_tags
  )

}

resource "aws_lb_listener" "alb_listener_port_443" {
  count = length( var.certificate_arn ) > 0 && var.load_balancer_type == "application" ? 1: 0

  load_balancer_arn = aws_lb.simple_lb.arn
  port              = "443"
  protocol          = "HTTPS"

  ssl_policy        = var.ssl_policy
  certificate_arn   = var.certificate_arn[0]

  default_action {
    type            = "fixed-response"
    fixed_response {
      content_type  = "text/html"
      message_body    = <<-EOT
        <html>
          <head>
            <title>Page not found</title>
            <style> h1 { text-align: center; text : Page Not Found} </style>
          </head>
          <body>
            <center>
              <h1>Page not found</h1>
            </center>
          </body>
        </html>
        EOT
      # message_body  = "<html lang='en'><head><title>Oops! Restricted Access</title><meta name='viewport' content='width=device-width,initial-scale=1><maximum-scale=1'/></head><body><main style=padding:0;margin:0;width:100vw;height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;font-family:Helvetica,sans-serif;font-size:14px'><style>body{margin:0}</style><section style='text-align:center'><img src='https://static.launchpad.tech.gov.sg/images/launchpad-error-logo.svg' alt='LaunchPad' width='150' height='150'/><h1 style='font-weight:600;margin-bottom:32px;margin-top:24px;font-size:34px'>Oops! Restricted Access.</h1><p style='margin:0;font-size:20px;line-height:1.6'>LaunchPad is only accessible within the government network.</p><p style='margin:0;font-size:20px;line-height:1.6'>If you are affected by this, please <a href='https://go.gov.sg/launchpad-gpt-feedback' style='text-underline-offset:4px;text-decoration:none;color:#344cbe'>reach out to us.</a></p></section></main></body></html>"
      status_code   = "404"
    }
  }

  tags = merge(
    {
      "type" = aws_lb.simple_lb.load_balancer_type == "application" ?  local.alb_prefix: local.nlb_prefix
      "scheme" = aws_lb.simple_lb.internal ? "private" : "public"
    },
    local.tags,
    var.additional_tags
  )
}

resource "aws_lb_listener_certificate" "certificate" {
  for_each = {
    for entry in var.certificate_arn : "${entry}" => entry
    if length( var.certificate_arn ) > 0 && var.load_balancer_type == "application"
  }

  listener_arn    = aws_lb_listener.alb_listener_port_443[0].arn
  certificate_arn = each.value
}

resource "aws_wafv2_web_acl_association" "web_acl" {
  count = var.web_acl_arn == null ? 0 : 1

  resource_arn = aws_lb.simple_lb.arn
  web_acl_arn  = var.web_acl_arn
}