locals {
  # test_security_group_ids = concat( data.aws_security_group.management_ez_ingress.*.id )
  test_security_group_ids = [ data.aws_security_group.management_ez["${local.secgrp_prefix}-${terraform.workspace}eztest-management"].id ]

  test_security_group_rules = [
################################################################################
# allow ssh from SEED
################################################################################
    {
      description       = "Allow inbound tcp 22 from SEED."
      type              = "ingress"
      protocol          = "tcp"
      from_port         = 22
      to_port           = 22
      cidr_blocks       = [ "8.29.230.18/32", "8.29.230.19/32" ]
    },
################################################################################    
# allow ssh from AWS
# https://docs.aws.amazon.com/cloud9/latest/user-guide/ip-ranges.html
# https://ip-ranges.amazonaws.com/ip-ranges.json
################################################################################    
    {
      description       = "Allow inbound tcp 22 from AWS."
      type              = "ingress"
      protocol          = "tcp"
      from_port         = 22
      to_port           = 22
      cidr_blocks       = [ "13.250.186.128/27", "13.250.186.160/27" ]
    },
################################################################################
# Allow 443 outbound to internet and workload.
################################################################################
    {
      description       = "Allow outbound to internet and workload."
      type              = "egress"
      protocol          = "tcp"
      from_port         = 80
      to_port           = 80
      cidr_blocks       = [ "0.0.0.0/0" ]
    },
    {
      description       = "Allow outbound to internet and workload."
      type              = "egress"
      protocol          = "tcp"
      from_port         = 443
      to_port           = 443
      cidr_blocks       = [ "0.0.0.0/0" ]
    },
################################################################################
# Allow 27017 outbound to workload.
################################################################################
    {
      description       = "Allow docdb outbound workload."
      type              = "egress"
      protocol          = "tcp"
      from_port         = 27017
      to_port           = 27017
      cidr_blocks       = [ "172.31.0.0/16", "172.30.0.0/16", "172.29.0.0/16" ]
    },
  ]

  test_security_group_ruleset = flatten(
    [for test_rule in local.test_security_group_rules :
      [for index in range( length( local.test_security_group_ids ) ) :
        {
          security_group_id = local.test_security_group_ids[ index ]
          description       = test_rule.description
          type              = test_rule.type
          protocol          = test_rule.protocol
          from_port         = test_rule.from_port
          to_port           = test_rule.to_port
          cidr_blocks       = test_rule.cidr_blocks
        }
      ]
    ]
  )
}

resource "aws_security_group_rule" "test" {
  for_each  = { for entry in local.test_security_group_ruleset: "${entry.security_group_id}.${entry.type}.${entry.protocol}.${entry.from_port}.${entry.to_port}.${entry.cidr_blocks[0]}" => entry }
    security_group_id = each.value.security_group_id
    description       = each.value.description
    type              = each.value.type
    protocol          = each.value.protocol
    from_port         = each.value.from_port
    to_port           = each.value.to_port
    cidr_blocks       = each.value.cidr_blocks
}
