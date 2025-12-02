# resource "aws_wafv2_web_acl_association" "waf_association" { # This is not for uat/prd blk
#   count = length( local.waf_association_arn )
#   resource_arn = local.waf_association_arn[count.index]
#   web_acl_arn  = aws_wafv2_web_acl.wafv2.arn
# }

########################################################################
########################################################################
# This section creates all the needed IP sets 
########################################################################
########################################################################
resource "aws_wafv2_ip_set" "any_ips_regional" {
  name               = "any_ips"

  description        = "All ipv4 addresses around the world."

  scope              = "REGIONAL"
  ip_address_version = "IPV4"
  # it cannot take in 0.0.0.0/0, so have to split into 2 sets of /1
  # addresses = formatlist("%s.0.0.0/8", range(0, 256))
  addresses = ["0.0.0.0/1", "128.0.0.0/1"]

  tags = merge(
    local.tags
  )
}

resource "aws_wafv2_ip_set" "internal_ips_regional" {
  name = "internal_ips"

  description        = "Internal IP addresses, to allow internal calls within the account."

  scope              = "REGIONAL"
  ip_address_version = "IPV4"

  addresses = concat(
    data.aws_vpc.sharedinfra_ez.cidr_block_associations.*.cidr_block,
    ["172.16.0.0/12"],
  )

  tags = merge(
    local.tags
  )
}

resource "aws_wafv2_ip_set" "whitelisted_ips_regional" {
  name = "whitelisted_ips"

  description        = "All the ip addresses we want to whitelist."

  scope              = "REGIONAL"
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
    var.whitelisted_ips.nhg
  )

  tags = merge(
    local.tags
  )
}

resource "aws_wafv2_ip_set" "whitelisted_ips_v6_regional" {
  name = "whitelisted_ips_v6"

  description        = "All the ip addresses we want to whitelist."

  scope              = "REGIONAL"
  ip_address_version = "IPV6"

  addresses = concat(
    var.whitelisted_ips.sis_gomax_v6,
    var.whitelisted_ips.seed_v6,
    var.whitelisted_ips.np_v6,
    var.whitelisted_ips.sp_v6,
    var.whitelisted_ips.rp_v6,
    var.whitelisted_ips.nyp_v6,
    var.whitelisted_ips.ite_v6,
    var.whitelisted_ips.moe_v6,
    var.whitelisted_ips.sportschool_v6,
    var.whitelisted_ips.mindef_v6,
    var.whitelisted_ips.nhg_v6,
  )

  tags = merge(
    local.tags
  )
}

resource "aws_wafv2_ip_set" "govtech_ips_regional" {
  name = "govtech_ips"

  description        = "GovTech IP, includes GSIB and SEED."

  scope              = "REGIONAL"
  ip_address_version = "IPV4"

  addresses = concat(
    var.whitelisted_ips.sis_gomax,
    var.whitelisted_ips.seed,
  )

  tags = merge(
    local.tags
  )
}

resource "aws_wafv2_ip_set" "govtech_ips_v6_regional" {
  name = "govtech_ips_v6"

  description        = "GovTech IP, includes GSIB and SEED."

  scope              = "REGIONAL"
  ip_address_version = "IPV6"

  addresses = concat(
    var.whitelisted_ips.sis_gomax_v6,
    var.whitelisted_ips.seed_v6,
  )

  tags = merge(
    local.tags
  )
}

resource "aws_wafv2_ip_set" "aibots_ips_regional" {
  name = "aibots_ips"

  description        = "IP addresses we want to allow to access AIbots."

  scope              = "REGIONAL"
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
    var.whitelisted_ips.nhg
  )

  tags = merge(
    local.tags
  )
}

########################################################################
########################################################################
# This is the REGIONAL WAFv2
########################################################################
########################################################################
resource "aws_wafv2_web_acl" "wafv2_regional" {
  description = "REGIONAL WAFv2 ACL for ${local.waf_name}"
  name        = "${local.waf_name}-regional"
  scope       = "REGIONAL"

  tags = merge(
    { "Name" = "${local.waf_name}-regional" },
    local.tags
  )

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.waf_name}-regional"
    sampled_requests_enabled   = true
  }

  ################################################################################
  ################################################################################
  # This part creates all the custom_response_body.
  # Need to split into 2 parts because they are based on different source
  ################################################################################
  ################################################################################
  # This creates all the pretty deny page based on local.products_regional
  ################################################################################
  dynamic "custom_response_body" {
    for_each = local.products_regional

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
        arn = aws_wafv2_ip_set.internal_ips_regional.arn
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "internal-allow-access-by-ip"
      sampled_requests_enabled   = true
    }
  }

  ################################################################################
  # This deny access to producs if they are not within the allowed IP
  ################################################################################
  dynamic "rule" {
    for_each = local.products_regional

    content {
      name     = "${replace(rule.value.search_string, ".", "_")}-deny-access-by-ip"
      # priority = 100 + index(local.products_regional, rule.value)
      priority = index(local.products_regional, rule.value) + 1

      action {
        # block {
        #   custom_response {
        #     custom_response_body_key = replace(rule.value.search_string, ".", "_")
        #     response_code            = 200
        #   }
        # }
        block {
          custom_response {
            response_code = 303
            response_header {
              name  = "Location"
              value = "https://public.${local.PUB_URL}/static/DenyAccess.html"
            }
          }
        }
      }

      statement {
        and_statement {
          statement {
            not_statement {
              statement {
                ip_set_reference_statement {
                  arn = rule.value.ip_set_arn
                }
              }
            }
          }

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
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "${replace(rule.value.search_string, ".", "_")}-deny-access-by-ip"
        sampled_requests_enabled   = true
      }
    }
  }

  ################################################################################
  # This deny all access that are not from the whitelisted ips
  ################################################################################
  rule {
    name     = "403-deny-access-by-ip"
    # priority = 199
    priority = length(local.products_regional) + 1

    action {
      block {
        custom_response {
          custom_response_body_key = "403_forbidden_access_by_network"
          response_code            = 403
        }
      }
    }

    statement {
      not_statement {
        statement {
          ip_set_reference_statement {
            arn = aws_wafv2_ip_set.whitelisted_ips_regional.arn
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "403_forbidden_access_by_network"
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
      # priority = 200 + index(local.Managed_Rule_Groups, rule.value)
      priority = length(local.products_regional) + length(["403-deny-access-by-ip"]) + index(local.Managed_Rule_Groups, rule.value) + 1

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
  ################################################################################
  # This creates all the allow_access_by_ip rule based on local.products_regional
  # i.e. ALLOW if from the whitelisted IP and going to project URL
  # THE DEFAULT BEHAVIOUR IS 404_page_not_found HENCE WE NEED these rule 300
  ################################################################################
  ################################################################################
  dynamic "rule" {
    for_each = local.products_regional

    content {
      name     = "${replace(rule.value.search_string, ".", "_")}-allow-access-by-ip"
      # priority = 300 + index(local.products_regional, rule.value)
      priority = length(local.products_regional) + length(["403-deny-access-by-ip"]) + length(local.Managed_Rule_Groups) + index(local.products_regional, rule.value) + 1

      action {
        allow {}
      }

      statement {
        and_statement {
          statement {
            ip_set_reference_statement {
              arn = rule.value.ip_set_arn
            }
          }

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
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "${replace(rule.value.search_string, ".", "_")}-allow-access-by-ip"
        sampled_requests_enabled   = true
      }
    }
  }
}

module "wafv2_regional" {
  source = "../modules/cloudwatch_log_group"

  name  = "aws-waf-logs-regional-${local.cw_log_name}"
  retention_in_days	= "${var.retention_in_days}"
  # destination_arn = data.aws_lambda_function.slack_notification.arn # KIV until we know what to filter
  #  filter_pattern = "${var.filter_pattern}" # KIV until we know what to filter

  tags = merge(
    local.tags,
    { name = "aws-waf-logs-regional-${local.cw_log_name}" }
  )
}

resource "aws_wafv2_web_acl_logging_configuration" "wafv2_regional" {
  log_destination_configs = [module.wafv2_regional.cloudwatch_log_group.arn]
  resource_arn            = aws_wafv2_web_acl.wafv2_regional.arn
}