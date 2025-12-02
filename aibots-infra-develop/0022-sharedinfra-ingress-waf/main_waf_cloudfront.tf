########################################################################
provider "aws" {
  alias  = "east"
  region = "us-east-1"
}

########################################################################
########################################################################
# This section creates all the needed IP sets 
########################################################################
########################################################################
resource "aws_wafv2_ip_set" "any_ips_cloudfront" {
  provider = aws.east
  name               = "any_ips"
  scope              = "CLOUDFRONT"

  ip_address_version = "IPV4"
  # it cannot take in 0.0.0.0/0, so have to split into 2 sets of /1
  # addresses = formatlist("%s.0.0.0/8", range(0, 256))
  addresses = ["0.0.0.0/1", "128.0.0.0/1"]

  tags = merge(
    local.tags
  )
}

resource "aws_wafv2_ip_set" "internal_ips_cloudfront" {
  provider = aws.east
  name = "internal_ips"
  scope              = "CLOUDFRONT"
  ip_address_version = "IPV4"

  addresses = concat(
    data.aws_vpc.sharedinfra_ez.cidr_block_associations.*.cidr_block,
    ["172.16.0.0/12"],
  )

  tags = merge(
    local.tags
  )
}

resource "aws_wafv2_ip_set" "whitelisted_ips_cloudfront" {
  provider = aws.east
  name = "whitelisted_ips"
  scope              = "CLOUDFRONT"
  ip_address_version = "IPV4"

  addresses = concat(
    var.whitelisted_ips.sis_gomax,
    var.whitelisted_ips.seed,
    var.whitelisted_ips.np,
    var.whitelisted_ips.sp,
    var.whitelisted_ips.rp,
    var.whitelisted_ips.nyp,
    var.whitelisted_ips.ite,
    var.whitelisted_ips.moe,
    var.whitelisted_ips.sportschool,
    var.whitelisted_ips.mindef,
    var.whitelisted_ips.nhg,
  )

  tags = merge(
    local.tags
  )
}

resource "aws_wafv2_ip_set" "govtech_ips_cloudfront" {
  provider = aws.east
  name = "govtech_ips"
  scope              = "CLOUDFRONT"
  ip_address_version = "IPV4"

  addresses = concat(
    var.whitelisted_ips.sis_gomax,
    var.whitelisted_ips.seed,
  )

  tags = merge(
    local.tags
  )
}

resource "aws_wafv2_ip_set" "aibots_ips_cloudfront" {
  provider = aws.east
  name = "aibots_ips"
  scope              = "CLOUDFRONT"
  ip_address_version = "IPV4"

  addresses = concat(
    var.whitelisted_ips.sis_gomax,
    var.whitelisted_ips.seed,
    var.whitelisted_ips.np,
    var.whitelisted_ips.sp,
    var.whitelisted_ips.rp,
    var.whitelisted_ips.nyp,
    var.whitelisted_ips.ite,
    var.whitelisted_ips.moe,
    var.whitelisted_ips.sportschool,
    var.whitelisted_ips.mindef,
    var.whitelisted_ips.nhg,
  )

  tags = merge(
    local.tags
  )
}

########################################################################
########################################################################
# This is the CLOUDFRONT WAFv2
########################################################################
########################################################################
resource "aws_wafv2_web_acl" "wafv2_cloudfront" {
  provider = aws.east

  description = "CLOUDFRONT WAFv2 ACL for ${local.waf_name}"
  name        = "${local.waf_name}-cloudfront"
  scope       = "CLOUDFRONT"

  tags = merge(
    { "Name" = "${local.waf_name}-cloudfront" },
    local.tags
  )

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.waf_name}-cloudfront"
    sampled_requests_enabled   = true
  }

  ################################################################################
  ################################################################################
  # This part creates all the custom_response_body.
  # Need to split into 2 parts because they are based on different source
  ################################################################################
  ################################################################################
  # This creates all the pretty deny page based on local.products_cloudfront_signed
  ################################################################################
  dynamic "custom_response_body" {
    for_each = local.products_cloudfront_signed

    content {
      content_type = custom_response_body.value.content_type
      content      = file("${path.module}/source/html/${custom_response_body.value.deny_page}")
      key          = replace(custom_response_body.value.search_string, ".", "_")
    }
  }
  ################################################################################
  # This creates all the html error page based on source/html/[0-9][0-9][0-9]_*.html
  ################################################################################
  dynamic "custom_response_body" {
    for_each = fileset("${path.module}/source/html", "[0-9][0-9][0-9]_*.html") # could use ** instead for a recursive search

    content {
      content      = file("${path.module}/source/html/${custom_response_body.value}")
      content_type = "TEXT_HTML"
      key          = replace(custom_response_body.value, ".html", "")
    }
  }

  ################################################################################
  # This is the default 404 error
  ################################################################################
  default_action {
    block {
      custom_response {
        custom_response_body_key = "404_page_not_found"
        response_code            = 404
      }
    }
  }

  ################################################################################
  ################################################################################
  # This part creates all the allow_access_by_ip rule.
  ################################################################################
  ################################################################################
  # This allows internal ip to access
  ################################################################################
  rule {
    name     = "internal-allow-access-by-ip"
    priority = 0 # priority starts with 0

    action {
      allow {}
    }

    statement {
      ip_set_reference_statement {
        arn = aws_wafv2_ip_set.internal_ips_cloudfront.arn
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "internal-allow-access-by-ip"
      sampled_requests_enabled   = true
    }
  }

  ################################################################################
  ################################################################################
  # These are the Managed_Rule_Groups
  ################################################################################
  ################################################################################
  dynamic "rule" {
    for_each = local.Managed_Rule_Groups

    content {
      name     = rule.value["name"]
      # priority = 100 + index(local.Managed_Rule_Groups, rule.value)
      priority = index(local.Managed_Rule_Groups, rule.value) + 1

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          name        = rule.value["name"]
          vendor_name = rule.value["vendor_name"]

          # This is to override the default AWS deny action
          # e.g. large body payload for upload
          dynamic "rule_action_override" {
            for_each = rule.value["count_override_name"]
            content {
              action_to_use {
                count {}
              }
              name = rule_action_override.value
            }
          }
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = rule.value["name"]
        sampled_requests_enabled   = true
      }
    }
  }

  ################################################################################
  # This allow access to public cloudfront if host is correct
  ################################################################################
  dynamic "rule" {
    for_each = local.products_cloudfront_public

    content {
      name     = "${replace(rule.value.search_string, ".", "_")}-allow-access-by-host-path"
      # priority = 200 + index(local.products_cloudfront_public, rule.value)
      priority = length(local.Managed_Rule_Groups) + index(local.products_cloudfront_public, rule.value) + 1

      action {
        allow {}
      }

      statement {
        and_statement {
          statement {
            byte_match_statement {
              positional_constraint = rule.value.positional_constraint
              search_string         = rule.value.search_string
      
              field_to_match {
                single_header {
                  name = "host"
                }
              }
      
              text_transformation {
                priority = 0
                type     = "COMPRESS_WHITE_SPACE"
              }
              text_transformation {
                priority = 1
                type     = "LOWERCASE"
              }
            }
          }
          statement {
            byte_match_statement {
              positional_constraint = "STARTS_WITH"
              search_string         = "/static/"
      
              field_to_match {
                uri_path {}
              }
      
              text_transformation {
                priority = 0
                type     = "COMPRESS_WHITE_SPACE"
              }
              text_transformation {
                priority = 1
                type     = "LOWERCASE"
              }
            }
          }
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "${replace(rule.value.search_string, ".", "_")}-allow-access-by-host-path"
        sampled_requests_enabled   = true
      }
    }
  }

  ################################################################################
  # This allow access to signed cookies cloudfront if the host and cookie are correct
  ################################################################################
  dynamic "rule" {
    for_each = local.products_cloudfront_signed

    content {
      name     = "${replace(rule.value.search_string, ".", "_")}-allow-access-by-signed_url"
      # priority = 300 + index(local.products_cloudfront_signed, rule.value)
      priority = length(local.Managed_Rule_Groups) + length(local.products_cloudfront_public) + index(local.products_cloudfront_signed, rule.value) + 1

      action {
        allow {}
      }

      statement {
        and_statement {
          statement {
            byte_match_statement {
              positional_constraint = rule.value.positional_constraint
              search_string         = rule.value.search_string
      
              field_to_match {
                single_header {
                  name = "host"
                }
              }
      
              text_transformation {
                priority = 0
                type     = "COMPRESS_WHITE_SPACE"
              }
              text_transformation {
                priority = 1
                type     = "LOWERCASE"
              }
            }
          }
          statement {
            size_constraint_statement {
              comparison_operator = "GT"
              size                = 0
      
              field_to_match {
                single_query_argument {
                  name = "expires"
                }
              }
      
              text_transformation {
                priority = 0
                type     = "NONE"
              }
            }
          }
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "${replace(rule.value.search_string, ".", "_")}-allow-access-by-signed_url"
        sampled_requests_enabled   = true
      }
    }
  }
}

resource "aws_cloudwatch_log_group" "wafv2_cloudfront" {
  provider = aws.east
  #checkov:skip=CKV_AWS_158: "Ensure that CloudWatch Log Group is encrypted by KMS"
    
  name  = "aws-waf-logs-cloudfront-${local.cw_log_name}"
  retention_in_days	= "${var.retention_in_days}"

  tags = merge(
    local.tags,
    { name = "aws-waf-logs-cloudfront-${local.cw_log_name}" }
  )
}



resource "aws_wafv2_web_acl_logging_configuration" "wafv2_cloudfront" {
  provider = aws.east

  log_destination_configs = [aws_cloudwatch_log_group.wafv2_cloudfront.arn]
  resource_arn            = aws_wafv2_web_acl.wafv2_cloudfront.arn
}