resource "aws_security_group" "alb_sso_outbound" {
  name        = "${local.secgrp_name}-sso"
  description = "${var.project_code} ${var.tier} alb sso outbound"
  vpc_id      = data.aws_vpc.sharedinfra_ez.id

  tags = merge(
    local.tags,
    { "Name"         = "${local.secgrp_name}-sso" },
    { "Project-Desc" = "${var.project_desc}-sso" },
  )
}

resource "aws_vpc_security_group_egress_rule" "alb_sso_outbound" {
  security_group_id = aws_security_group.alb_sso_outbound.id

  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
  description = "Allow ALB to go to AWS backbone for OIDC Authentication"
}

module "private_alb" {
  source = "../modules/lb"

  name   = "${var.project_code}-pte"
  internal      = true
  load_balancer_type = "application"

  vpc_id = data.aws_vpc.sharedinfra_ez.id
  subnet_ids = [
    data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-a-${terraform.workspace}ezdmz-sharedinfra"].id,
    data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-b-${terraform.workspace}ezdmz-sharedinfra"].id,
  ]
  security_group_ids = [
    data.aws_security_group.sharedinfra_ez["${local.secgrp_prefix}-${terraform.workspace}ezdmz-sharedinfra"].id,
    aws_security_group.alb_sso_outbound.id,
  ]

  enable_deletion_protection = true
  force_destroy = false # this is a test environment, true for s3 easy destroy.
  ssl_policy    = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn = var.certificate_arn
  idle_timeout = 900

  aws_s3_bucket_logging = data.aws_s3_bucket.access-logs-s3.id

  access_logs = {
    bucket = data.aws_s3_bucket.access-logs-elb.id
    # prefix = "${var.project_code}-pte"
  }

  web_acl_arn  = data.aws_wafv2_web_acl.sharedinfra_ez_regional.arn

  tags = local.tags
}

resource "aws_lb_listener_rule" "private_alb_443" {
  # lifecycle {
  #   ignore_changes = [
  #     priority,
  #   ]
  # }

  # this is for NLB to healthcheck
  listener_arn = module.private_alb.listener_port_443.arn
  priority   = 1

  tags = merge(
    local.tags,
    {
      "Name" = "${local.alb_lsnr_rule_name}-heartbeat",
    }
  )

  action {
    type              = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "For nlb healthcheck"
      status_code  = "200"
    }
  }
  condition {
    path_pattern {
      values = [ "/lb/heartbeat" ]
    }
  }
}

resource "aws_lb_listener_rule" "maintenance" {
  # this is something that you have to click ops
  lifecycle {
    ignore_changes = [
      condition,
    ]
  }

  # this is for NLB to healthcheck
  listener_arn = module.private_alb.listener_port_443.arn
  priority   = 2

  tags = merge(
    local.tags,
    {
      "Name" = "${local.alb_lsnr_rule_name}-maintenance",
    }
  )

  action {
    type              = "fixed-response"
    fixed_response {
      content_type = "text/html"
      message_body = "<html><head><title>Maintenance</title><style>h1{text-align:center;text :Maintenance}</style></head><body><center><h1>We are having a scheduled maintenance.<br>Please try again later, thank you.</h1></center></body></html>"
      status_code  = "200"
    }
  }
  condition {
    host_header {
      values = [
        # "${local.route53_zone_prefix}*", # for maintenance
        # "${local.route53_zone_prefix}aibots.gov.sg", # for maintenance
        "nonexistence.domain", # for normal day
      ]
    }
  }
  condition {
    source_ip {
      values = [
        "8.8.8.8/32", # for maintenance
        # "0.0.0.0/0", # for normal day
      ]
    }
  }
}
