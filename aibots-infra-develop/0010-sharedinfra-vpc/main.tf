################################################################################
# input to locals has to be FIX, e.g. variable, or resources already created.
################################################################################
locals {
  subnet = distinct(
    flatten(
      [for subnet in var.subnets :
        [for index in range(length(subnet.cidr_blocks)) :
          {
            name               = subnet.name
            tier               = subnet.tier
            az                 = index == 0 ? "a" : index == 1 ? "b" : "c"
            cidr_block         = subnet.cidr_blocks[index]
            share_route_table  = subnet.share_route_table
            assign_public_ipv4 = subnet.assign_public_ipv4
          }
        ]
      ]
    )
  )

  route_table = distinct(
    flatten(
      [for subnet in var.subnets :
        [for index in range(length(subnet.cidr_blocks)) :
          {
            tier = subnet.tier
            az   = subnet.share_route_table == true ? "*" : index == 0 ? "a" : index == 1 ? "b" : "c"
          }
        ]
      ]
    )
  )
}
################################################################################
# data can be something dynamic that is new and to be created. However, remember to use depends_on.
################################################################################
data "aws_subnets" "project" {
  depends_on = [aws_subnet.project]
  for_each   = { for entry in var.subnets : "${entry.tier}" => entry }
  filter {
    name   = "tag:Project-Code"
    values = [var.project_code]
  }
  filter {
    name   = "tag:Zone"
    values = [var.zone]
  }
  filter {
    name   = "tag:Tier"
    values = [each.value.tier]
  }
}
################################################################################
#creating the resources
################################################################################
locals {
  vpc_id = var.vpc_cidr_block == null ? data.aws_vpc.sharedinfra_ez.id : aws_vpc.project[0].id
}

resource "aws_subnet" "project" {
  for_each                = { for entry in local.subnet : "${entry.name}.${entry.az}" => entry }
  vpc_id                  = local.vpc_id
  cidr_block              = each.value.cidr_block
  availability_zone       = "ap-southeast-1${each.value.az}"
  map_public_ip_on_launch = each.value.assign_public_ipv4
  tags = merge(
    local.tags,
    {
      "Name" = substr("${local.subnet_prefix}-${each.value.az}-${terraform.workspace}${var.zone}${each.value.tier}-${var.project_code}", 0, 256)
      "Tier" = each.value.tier
      "az"   = each.value.az
    }
  )
}

resource "aws_route_table" "project" {
  for_each = { for entry in local.route_table : "${entry.tier}.${entry.az}" => entry }
  vpc_id   = local.vpc_id

  tags = merge(
    local.tags,
    {
      "Name" = substr("${local.routetable_prefix}-${each.value.az}-${terraform.workspace}${var.zone}${each.value.tier}-${var.project_code}", 0, 256)
      "Tier" = each.value.tier
      "az"   = each.value.az
    }
  )
}

resource "aws_route_table_association" "project" {
  for_each       = { for entry in local.subnet : "${entry.tier}.${entry.az}" => entry }
  route_table_id = aws_route_table.project["${each.value.tier}.${each.value.share_route_table == true ? "*" : each.value.az}"].id
  subnet_id      = aws_subnet.project["${each.value.tier}.${each.value.az}"].id
}

resource "aws_network_acl" "project" {
  for_each   = { for entry in var.subnets : "${entry.tier}" => entry }
  vpc_id     = local.vpc_id
  subnet_ids = data.aws_subnets.project[each.value.tier].ids

  tags = merge(
    local.tags,
    {
      "Name" = substr("${local.nacl_prefix}-${terraform.workspace}${var.zone}${each.value.tier}-${var.project_code}", 0, 256)
      "Tier" = each.value.tier
    }
  )
}

resource "aws_security_group" "project" {
  for_each    = { for entry in var.subnets : "${entry.tier}" => entry }
  name        = substr("${local.secgrp_prefix}-${terraform.workspace}${var.zone}${each.value.tier}-${var.project_code}", 0, 256)
  description = "${var.project_code} ${each.value.tier}"
  vpc_id      = local.vpc_id

  tags = merge(
    local.tags,
    {
      "Name" = substr("${local.secgrp_prefix}-${terraform.workspace}${var.zone}${each.value.tier}-${var.project_code}", 0, 255)
      "Tier" = each.value.tier
    }
  )
}

resource "aws_internet_gateway" "igw" {
  count = var.deploy_igw ? 1 : 0

  vpc_id = local.vpc_id

  tags = merge(
    { "Name" = "${local.igw_name}" },
    local.tags
  )
}
