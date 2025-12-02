locals{
# always add to the bottom of the list.
# else it will destroy and create, and you will have to wait.
# if you are deleting from the list, do it via the console, disassociate from the firewall_policy.

  # setting project-desc here because there are too many components in 1 NFW resource.
  # all the components uses project-desc as part of the naming.
  # this cannot go into the var because var cannot take in variables.
  project-desc = "network firewall"

  whitelisted_domains = [
    {
      name = "aws-alb-auth"
      targets = [
                  "public-keys.auth.elb.ap-southeast-1.amazonaws.com",
#                  "${terraform.workspace}-sso-dsaid.auth.ap-southeast-1.amazoncognito.com"
                ]
      target_types    = [ "TLS_SNI", ]
      HOME_NET  = concat(
        # data.aws_vpc.sharedinfra_ez.cidr_block_associations.*.cidr_block,
        data.aws_vpc.sharedsvc_ez.cidr_block_associations.*.cidr_block,
        data.aws_vpc.aibots_ez.cidr_block_associations.*.cidr_block,
      )
    },
    {
      name = "aws-endpoint"
      targets = [
                  "email-smtp.ap-southeast-1.amazonaws.com", # emails already traverse in internet, no need to waste money
                ]
      target_types    = [ "TLS_SNI", ]
      HOME_NET  = concat(
        data.aws_vpc.sharedsvc_ez.cidr_block_associations.*.cidr_block,
      )
    },
    # { # we have put the notification lambda out of VPC, so this is not needed.
    #   name = "hooks-slack-com"
    #   targets = ["hooks.slack.com"]
    #   target_types    = [ "TLS_SNI", ]
    #   HOME_NET  = concat(
    #     data.aws_vpc.sharedsvc_ez.cidr_block_associations.*.cidr_block,
    #   )
    # },
    {
      name = "govtech-sharedsvc-aoai"
      targets = [
                  "moonshot-aoai-sg-endpoint.azure-api.net",
                ]
      target_types    = [ "TLS_SNI", ]
      HOME_NET  = concat(
        data.aws_vpc.sharedsvc_ez.cidr_block_associations.*.cidr_block,
      )
    },
    {
      name = "aoai-tiktoken"
      targets = [
                  "openaipublic.blob.core.windows.net"
                ]
      target_types    = [ "TLS_SNI", ]
      HOME_NET  = concat(
        # data.aws_vpc.sharedinfra_ez.cidr_block_associations.*.cidr_block,
        data.aws_vpc.sharedsvc_ez.cidr_block_associations.*.cidr_block,
        data.aws_vpc.aibots_ez.cidr_block_associations.*.cidr_block,
      )
    },
    {
      name = "latios"
      targets = [
                  # "latios-api.data.tech.gov.sg",
                  "latios-api.${local.route53_zone_prefix}data.tech.gov.sg",
                ]
      target_types    = [ "TLS_SNI", ]
      HOME_NET  = concat(
        # data.aws_vpc.sharedinfra_ez.cidr_block_associations.*.cidr_block,
        data.aws_vpc.sharedsvc_ez.cidr_block_associations.*.cidr_block,
        data.aws_vpc.aibots_ez.cidr_block_associations.*.cidr_block,
      )
    },
    {
      name = "govtech-llmstack"
      targets = [
                  "api.stack.govtext.gov.sg", var.govtech_llmstack_endpoint,
                ]
      target_types    = [ "TLS_SNI", ]
      HOME_NET  = concat(
        data.aws_vpc.aibots_ez.cidr_block_associations.*.cidr_block,
      )
    },
    {
      name = "rag"
      targets = [
                  # "latios-api.data.tech.gov.sg",
                  "packages.unstructured.io", "unstructured.io", "raw.githubusercontent.com", "huggingface.co", "cdn-lfs.huggingface.co",
                  "aoss.ap-southeast-1.amazonaws.com" # aoss-picker needs to aoss_client.list_collections as there is no vpce
                ]
      target_types    = [ "TLS_SNI", ]
      HOME_NET  = concat(
        # data.aws_vpc.sharedinfra_ez.cidr_block_associations.*.cidr_block,
        data.aws_vpc.aibots_ez.cidr_block_associations.*.cidr_block,
      )
    },
    {
      name = "govtech-govtext"
      targets = [
                  var.govtech_govtext_endpoint,
                ]
      target_types    = [ "TLS_SNI", ]
      HOME_NET  = concat(
        # data.aws_vpc.sharedinfra_ez.cidr_block_associations.*.cidr_block,
        data.aws_vpc.aibots_ez.cidr_block_associations.*.cidr_block,
      )
    },
  ]
}

resource "aws_networkfirewall_rule_group" "domains" {
  for_each = { for entry in local.whitelisted_domains: entry.name => entry }

  name     = each.value.name # "STATEFUL-ALLOW-google-443"
  description  = "Stateful rule to allow ${each.value.name}"
  type     = "STATEFUL"
  capacity   = 100

  tags = merge(
    local.tags,
    {
      "Name"= "${local.nfw_name}-rule-${each.value.name}"
      "project-desc" = local.project-desc
    }
  )

  rule_group {
    rules_source {
      rules_source_list {
        generated_rules_type = "ALLOWLIST"
        target_types    = each.value.target_types
        targets         = each.value.targets
      }
    }

    rule_variables {
      ip_sets {
        key = "HOME_NET"
        ip_set {
          definition = each.value.HOME_NET
        }
      }
    }
  }
}
# resource "aws_networkfirewall_rule_group" "domains" {
#   count = length( local.whitelisted_domains )

#   name     = local.whitelisted_domains[count.index].name # "STATEFUL-ALLOW-google-443"
#   description  = "Stateful rule to allow ${local.whitelisted_domains[count.index].name}"
#   type     = "STATEFUL"
#   capacity   = 100

#   tags = merge(
#     local.tags,
#     {
#       "Name"= "${local.nfw_name}-rule-${local.whitelisted_domains[count.index].name}"
#       "project-desc" = local.project-desc
#     }
#   )

#   rule_group {
#     rules_source {
#       rules_source_list {
#         generated_rules_type = "ALLOWLIST"
#         target_types    = local.whitelisted_domains[count.index].target_types
#         targets         = local.whitelisted_domains[count.index].targets
#       }
#     }

#     rule_variables {
#       ip_sets {
#         key = "HOME_NET"
#         ip_set {
#           definition = local.whitelisted_domains[count.index].HOME_NET
#         }
#       }
#     }
#   }
# }

resource "aws_networkfirewall_firewall_policy" "whitelisted_domains_policy" {
  name     = "${local.nfw_name}-policy-whitelisted-domains"

  tags = merge(
    local.tags,
    {
      "Name" = "${local.nfw_name}-policy-whitelisted-domains",
      "project-desc" = local.project-desc
    }
  )

  depends_on = [ aws_networkfirewall_rule_group.domains ]

  firewall_policy {
    stateful_default_actions     = [ ]
    stateless_default_actions    = [ "aws:forward_to_sfe", ]
    stateless_fragment_default_actions = [ "aws:forward_to_sfe", ]

    dynamic "stateful_rule_group_reference" {
      for_each = aws_networkfirewall_rule_group.domains

      content {
        resource_arn = stateful_rule_group_reference.value.arn
      }
    }
  }
}

resource "aws_networkfirewall_firewall" "nfw" {
  name                  = local.nfw_name
  description           = "Forward Proxy with ${local.nfw_name}"
  vpc_id                = data.aws_vpc.sharedinfra_ez.id

  subnet_mapping {
    subnet_id = data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-${local.az_deployment}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id
  }

  firewall_policy_arn       = aws_networkfirewall_firewall_policy.whitelisted_domains_policy.arn
  firewall_policy_change_protection = false
  delete_protection         = true
  subnet_change_protection  = false

  tags = merge(
    local.tags,
    {
      "Name" = local.nfw_name,
      "project-desc" = local.project-desc,
    }
  )
}

resource "aws_networkfirewall_logging_configuration" "nfw" {
  firewall_arn = aws_networkfirewall_firewall.nfw.arn
  logging_configuration {
    log_destination_config {
      log_destination = {
        # logGroup = aws_cloudwatch_log_group.nfw.name
        logGroup = module.nfw.cloudwatch_log_group.name
      }
      log_destination_type = "CloudWatchLogs"
      log_type             = "FLOW"
    }
    log_destination_config {
      log_destination = {
        # logGroup = aws_cloudwatch_log_group.nfw.name
        logGroup = module.nfw.cloudwatch_log_group.name
      }
      log_destination_type = "CloudWatchLogs"
      log_type             = "ALERT"
    }
  }
}

module "nfw" {
  source = "../modules/cloudwatch_log_group"

  name  = "/aws/vpc-flow-log/nfw-${local.cw_log_name}"
  retention_in_days	= "${var.retention_in_days}"
  destination_arn = data.aws_lambda_function.notification.arn # KIV until we know what to filter
  filter_pattern = "${var.filter_pattern}" # KIV until we know what to filter

  tags = merge(
    local.tags,
    {
      "Name" = "/aws/nfw-log/nfw-${local.cw_log_name}"
      "project-desc" = local.project-desc      
    }
  )
}