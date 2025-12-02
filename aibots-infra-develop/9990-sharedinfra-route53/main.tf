locals{
  all_route53_zone = concat(local.all_endpoints, [ data.aws_route53_zone.aibots_gov_sg.name ], )
}

data "aws_route53_zone" "all" {
  count = length( local.all_route53_zone )
  name = local.all_route53_zone[count.index]
  private_zone = true

  tags = {
    Environment = terraform.workspace
  }
}

locals{
  sub_vpc   = [
                data.aws_vpc.sharedsvc_ez,
                data.aws_vpc.management_ez,
                data.aws_vpc.aibots_ez,
              ]

  vpc_association = distinct(
    flatten(
      [for vpc in local.sub_vpc :
        [for zone in data.aws_route53_zone.all :
          {
            vpc_id = vpc.id
            zone_id = zone.zone_id
          }
        ]
      ]
    )
  )
}

resource "aws_route53_zone_association" "secondary" {
  for_each  = { for entry in local.vpc_association: "${entry.vpc_id}.${entry.zone_id}" => entry }

  vpc_id  = each.value.vpc_id
  zone_id = each.value.zone_id
}

resource "aws_route53_resolver_rule" "system" {
  for_each  = { for entry in local.all_route53_zone: "${entry}" => entry }

  name = replace( each.value, ".", "_")
  domain_name = each.value
  rule_type   = "SYSTEM"

  tags = merge(
    local.tags,
    {
      "Name" = replace( each.value, ".", "_")
    }
  )
}