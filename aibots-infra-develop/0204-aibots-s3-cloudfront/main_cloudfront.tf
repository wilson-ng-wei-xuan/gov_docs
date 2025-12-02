locals {
  s3_origin_id = "${data.aws_caller_identity.current.account_id}-${var.project_code}-${var.project_desc}"
}

resource "aws_cloudfront_origin_access_control" "project" {
  name                              = "${terraform.workspace}${var.zone}${var.tier}-${var.project_code}-${var.project_desc}"
  description                       = "Signing Policy"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}


resource "aws_cloudfront_public_key" "project" {
  lifecycle {
    ignore_changes = [
      comment, encoded_key
    ]
  }

# secret rotation will delete the old key as AWS only allow 10 keys
# terraform apply will always re-create the key
# so this key will alway be created, but after the second run it will not be in use anymore.
  count = var.secret_rotation == false ? 0 : 1

  name        = "${terraform.workspace}${var.zone}${var.tier}-${var.project_code}-${var.project_desc}-terraform"
  comment     = "${local.today_local}"
  encoded_key = tls_private_key.project[0].public_key_pem
}


resource "aws_cloudfront_key_group" "project" {
  count = var.secret_rotation == false ? 0 : 1

  lifecycle {
    ignore_changes = [
      items,
    ]
  }

  name    = "${terraform.workspace}${var.zone}${var.tier}-${var.project_code}-${var.project_desc}"
  comment = "Public Keys for ${terraform.workspace}${var.zone}${var.tier}-${var.project_code}-${var.project_desc}"
  items   = [aws_cloudfront_public_key.project[0].id]
}


data "aws_cloudfront_cache_policy" "project" {
  name = "Managed-CachingOptimized"
}


data "aws_cloudfront_response_headers_policy" "project" {
  name = "Managed-CORS-with-preflight-and-SecurityHeadersPolicy"
}

resource "aws_cloudfront_distribution" "project" {
  default_cache_behavior {
    trusted_key_groups     = [ aws_cloudfront_key_group.project[0].id ]

    smooth_streaming           = true

    cache_policy_id            = data.aws_cloudfront_cache_policy.project.id
    response_headers_policy_id = data.aws_cloudfront_response_headers_policy.project.id

    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = local.s3_origin_id

    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    compress               = true
    viewer_protocol_policy = "redirect-to-https"
  }

  ordered_cache_behavior {
    trusted_key_groups         = []
    trusted_signers            = []

    cache_policy_id            = data.aws_cloudfront_cache_policy.project.id # "658327ea-f89d-4fab-a63d-7e88639e58f6"
    response_headers_policy_id = data.aws_cloudfront_response_headers_policy.project.id # "eaab4381-ed33-4a86-88ca-d9558dc6cd63"

    allowed_methods            = [ "GET", "HEAD", "OPTIONS" ]
    cached_methods             = [ "GET", "HEAD", "OPTIONS" ]
    target_origin_id           = local.s3_origin_id

    min_ttl                    = 0
    default_ttl                = 0
    max_ttl                    = 0
    compress                   = true

    path_pattern               = "/static/*"
    smooth_streaming           = true
    viewer_protocol_policy     = "redirect-to-https"
  }

  origin {
    domain_name              = module.s3-cloudfront.bucket.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.project.id
    origin_id                = local.s3_origin_id
    origin_path              = var.origin_path
  }

  enabled             = true
  is_ipv6_enabled     = true
  # you need to create the cert manager in NV.
  aliases = ["public.${local.route53_zone_prefix}${var.domain}"]
  # comment             = "${terraform.workspace}${var.zone}${var.tier}-${var.project_code}-${var.project_desc}"
  comment             = "public.${local.route53_zone_prefix}${var.domain}"
  default_root_object = "index.html"

  logging_config {
    include_cookies = false
    bucket          = "${data.aws_s3_bucket.access-logs-cloudfront.bucket}.s3.amazonaws.com"
    prefix          = "public.${local.route53_zone_prefix}${var.domain}"
  }

  viewer_certificate {
    acm_certificate_arn            = var.acm_certificate_arn
    cloudfront_default_certificate = false
    minimum_protocol_version       = "TLSv1.2_2021"
    ssl_support_method             = "sni-only"
  }

  price_class = "PriceClass_200"

  web_acl_id = data.aws_wafv2_web_acl.sharedinfra_ez_cloudfront.arn

  # Relaxing WAF access restrictions so all whitelisted IPs and
  # domains can connect globally.
  # restrictions {
  #   geo_restriction {
  #     restriction_type = "whitelist"
  #     locations        = ["SG"]
  #   }
  # }
  restrictions { 
    geo_restriction {
      restriction_type = "none"
      locations        = []
    }
  }

  tags = local.tags
}