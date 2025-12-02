resource "aws_vpc" "project" {
  count = var.vpc_cidr_block == null ? 0 : 1

  cidr_block = var.vpc_cidr_block

  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(
    local.tags,
    { "Name" = local.vpc_name }
  )
}
