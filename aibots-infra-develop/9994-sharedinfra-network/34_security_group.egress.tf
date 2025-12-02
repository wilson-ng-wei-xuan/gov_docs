locals {
  # egress_security_group_ids = concat( data.aws_security_group.sharedinfra_ez_egress.*.id )
  egress_security_group_ids = concat( [ data.aws_security_group.sharedinfra_ez["${local.secgrp_prefix}-${terraform.workspace}ezegress-sharedinfra"].id ] )

  egress_security_group_rules = [
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
      description       = "Allow inbound tcp 443 from app."
      type              = "ingress"
      protocol          = "tcp"
      from_port         = 443
      to_port           = 443
      cidr_blocks       = local.subnet_inspect
    },
    {
      description       = "Allow outbound tcp 443 to Internet."
      type              = "egress"
      protocol          = "tcp"
      from_port         = 443
      to_port           = 443
      cidr_blocks       = [ "0.0.0.0/0" ]
    },
    {
      description       = "Allow outbound tcp 443 to endpt."
      type              = "egress"
      protocol          = "tcp"
      from_port         = 443
      to_port           = 443
      cidr_blocks       = local.subnet_endpt
    },
  ]

  # egress_security_group_ruleset = distinct(
  #   flatten(
  #     [for egress_rule in local.egress_security_group_rules :
  #       [for index in range( length( local.egress_security_group_ids ) ) :
  #         {
  #           security_group_id = local.egress_security_group_ids[ index ]
  #           description       = egress_rule.description
  #           type              = egress_rule.type
  #           protocol          = egress_rule.protocol
  #           from_port         = egress_rule.from_port
  #           to_port           = egress_rule.to_port
  #           cidr_blocks       = egress_rule.cidr_blocks
  #         }
  #       ]
  #     ]
  #   )
  # )
  egress_security_group_ruleset = flatten(
    [for egress_rule in local.egress_security_group_rules :
      [for index in range( length( local.egress_security_group_ids ) ) :
        {
          security_group_id = local.egress_security_group_ids[ index ]
          description       = egress_rule.description
          type              = egress_rule.type
          protocol          = egress_rule.protocol
          from_port         = egress_rule.from_port
          to_port           = egress_rule.to_port
          cidr_blocks       = egress_rule.cidr_blocks
        }
      ]
    ]
  )
}

resource "aws_security_group_rule" "egress" {
  for_each  = { for entry in local.egress_security_group_ruleset: "${entry.security_group_id}.${entry.type}.${entry.protocol}.${entry.from_port}.${entry.to_port}.${entry.cidr_blocks[0]}" => entry }
    security_group_id = each.value.security_group_id
    description       = each.value.description
    type              = each.value.type
    protocol          = each.value.protocol
    from_port         = each.value.from_port
    to_port           = each.value.to_port
    cidr_blocks       = each.value.cidr_blocks
}
