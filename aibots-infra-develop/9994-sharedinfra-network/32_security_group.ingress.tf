locals {
  # ingress_security_group_ids = concat( data.aws_security_group.sharedinfra_ez_ingress.*.id )
  ingress_security_group_ids = [ data.aws_security_group.sharedinfra_ez["${local.secgrp_prefix}-${terraform.workspace}ezingress-sharedinfra"].id ]

  ingress_security_group_rules = [
################################################################################
# Allow inbound from Internet
################################################################################
    {
      description       = "Allow inbound tcp 80 from Internet."
      type              = "ingress"
      protocol          = "tcp"
      from_port         = 80
      to_port           = 80
      cidr_blocks       = [ "0.0.0.0/0" ]
    },
    {
      description       = "Allow inbound tcp 443 from Internet."
      type              = "ingress"
      protocol          = "tcp"
      from_port         = 443
      to_port           = 443
      cidr_blocks       = [ "0.0.0.0/0" ]
    },
################################################################################
# Allow outbound to ALB in dmz
################################################################################
    {
      description       = "Allow outbound tcp 80 for NLB to ALB forwarding."
      type              = "egress"
      protocol          = "tcp"
      from_port         = 80
      to_port           = 80
      cidr_blocks       = local.subnet_dmz
    },
    {
      description       = "Allow outbound tcp 443 for NLB to ALB forwarding."
      type              = "egress"
      protocol          = "tcp"
      from_port         = 443
      to_port           = 443
      cidr_blocks       = local.subnet_dmz
    },
# ################################################################################
# # Allow outbound to endpoints.
# ################################################################################
#     {
#       description       = "Allow outbound tcp 443 to endpt."
#       type              = "egress"
#       protocol          = "tcp"
#       from_port         = 443
#       to_port           = 443
#       cidr_blocks       = local.subnet_endpt
#     },
  ]

  ingress_security_group_ruleset = flatten(
    [for ingress_rule in local.ingress_security_group_rules :
      [for index in range( length( local.ingress_security_group_ids ) ) :
        {
          security_group_id = local.ingress_security_group_ids[ index ]
          description       = ingress_rule.description
          type              = ingress_rule.type
          protocol          = ingress_rule.protocol
          from_port         = ingress_rule.from_port
          to_port           = ingress_rule.to_port
          cidr_blocks       = ingress_rule.cidr_blocks
        }
      ]
    ]
  )
}

resource "aws_security_group_rule" "ingress" {
  for_each  = { for entry in local.ingress_security_group_ruleset: "${entry.security_group_id}.${entry.type}.${entry.protocol}.${entry.from_port}.${entry.to_port}.${entry.cidr_blocks[0]}" => entry }
    security_group_id = each.value.security_group_id
    description       = each.value.description
    type              = each.value.type
    protocol          = each.value.protocol
    from_port         = each.value.from_port
    to_port           = each.value.to_port
    cidr_blocks       = each.value.cidr_blocks
}
