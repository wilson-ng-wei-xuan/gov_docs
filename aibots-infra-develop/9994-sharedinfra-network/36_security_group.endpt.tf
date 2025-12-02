locals {
  # endpt_security_group_ids = concat( data.aws_security_group.sharedinfra_ez_endpt.*.id )
  endpt_security_group_ids = concat( [ data.aws_security_group.sharedinfra_ez["${local.secgrp_prefix}-${terraform.workspace}ezendpt-sharedinfra"].id ] )

  endpt_security_group_rules = [
    # {
    #   description       = "TESTING ONLY."
    #   type              = "ingress"
    #   protocol          = "tcp"
    #   from_port         = 0
    #   to_port           = 65535
    #   cidr_blocks       = [ "0.0.0.0/0" ]
    # },
    # {
    #   description       = "TESTING ONLY."
    #   type              = "egress"
    #   protocol          = "tcp"
    #   from_port         = 0
    #   to_port           = 65535
    #   cidr_blocks       = [ "0.0.0.0/0" ]
    # },

    {
      description       = "Allow inbound from VPC."
      type              = "ingress"
      protocol          = "tcp"
      from_port         = 443
      to_port           = 443
      cidr_blocks       = local.cidr_all
    },
    {
      description       = "Allow outbound tcp 443 to endpoints backbone."
      type              = "egress"
      protocol          = "tcp"
      from_port         = 443
      to_port           = 443
      cidr_blocks       = [ "0.0.0.0/0" ]
    },
  ]

  # endpt_security_group_ruleset = distinct(
  #   flatten(
  #     [for endpt_rule in local.endpt_security_group_rules :
  #       [for index in range( length( local.endpt_security_group_ids ) ) :
  #         {
  #           security_group_id = local.endpt_security_group_ids[ index ]
  #           description       = endpt_rule.description
  #           type              = endpt_rule.type
  #           protocol          = endpt_rule.protocol
  #           from_port         = endpt_rule.from_port
  #           to_port           = endpt_rule.to_port
  #           cidr_blocks       = endpt_rule.cidr_blocks
  #         }
  #       ]
  #     ]
  #   )
  # )
  endpt_security_group_ruleset = flatten(
    [for endpt_rule in local.endpt_security_group_rules :
      [for index in range( length( local.endpt_security_group_ids ) ) :
        {
          security_group_id = local.endpt_security_group_ids[ index ]
          description       = endpt_rule.description
          type              = endpt_rule.type
          protocol          = endpt_rule.protocol
          from_port         = endpt_rule.from_port
          to_port           = endpt_rule.to_port
          cidr_blocks       = endpt_rule.cidr_blocks
        }
      ]
    ]
  )
}

resource "aws_security_group_rule" "endpt" {
  for_each  = { for entry in local.endpt_security_group_ruleset: "${entry.security_group_id}.${entry.type}.${entry.protocol}.${entry.from_port}.${entry.to_port}.${entry.cidr_blocks[0]}" => entry }
    security_group_id = each.value.security_group_id
    description       = each.value.description
    type              = each.value.type
    protocol          = each.value.protocol
    from_port         = each.value.from_port
    to_port           = each.value.to_port
    cidr_blocks       = each.value.cidr_blocks
}
