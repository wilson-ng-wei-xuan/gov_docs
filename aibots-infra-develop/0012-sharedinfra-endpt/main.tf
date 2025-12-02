module "interface_endpoints" {
  source = "../modules/endpoints"

  interface_endpt = var.interface_endpts

  vpc_id              = data.aws_vpc.sharedinfra_ez.id
  # private_dns_enabled = false # false if you are doing endpoint sharing, and you need all the route53
  subnet_ids = [
    data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-${local.az_deployment}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id
  ]
  security_group_ids = [
    data.aws_security_group.sharedinfra_ez["${local.secgrp_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id
  ]

  tags = local.tags
}