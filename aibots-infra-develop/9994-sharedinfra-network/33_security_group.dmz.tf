locals {
  # dmz_security_group_ids = concat( data.aws_security_group.sharedinfra_ez_dmz.*.id )
  dmz_security_group_ids = [ data.aws_security_group.sharedinfra_ez["${local.secgrp_prefix}-${terraform.workspace}ezdmz-sharedinfra"].id ]

  dmz_security_group_rules = [
################################################################################
# Allow inbound for NLB to ALB forwarding.
# while on paper, it seems we only need to allow the ingress IP, but:
# - NLB targetting ALB, will turn on Preserve Client IP,
# - ALB access logs will show public IP
# - AWS magic will still return the traffic back to the NLB as "real" source
# - this will prevent the asyn routing
################################################################################
    {
      description       = "Allow outbound tcp 80 for NLB to ALB forwarding."
      type              = "ingress"
      protocol          = "tcp"
      from_port         = 80
      to_port           = 80
      cidr_blocks       = [ "0.0.0.0/0" ]
    },
    {
      description       = "Allow outbound tcp 443 for NLB to ALB forwarding."
      type              = "ingress"
      protocol          = "tcp"
      from_port         = 443
      to_port           = 443
      cidr_blocks       = [ "0.0.0.0/0" ]
    },
################################################################################
# Allow outbound to app.
################################################################################
    {
      description       = "Allow outbound tcp 443 to app."
      type              = "egress"
      protocol          = "tcp"
      from_port         = 443
      to_port           = 443
      cidr_blocks       = local.subnet_app
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

  dmz_security_group_ruleset = flatten(
    [for dmz_rule in local.dmz_security_group_rules :
      [for index in range( length( local.dmz_security_group_ids ) ) :
        {
          security_group_id = local.dmz_security_group_ids[ index ]
          description       = dmz_rule.description
          type              = dmz_rule.type
          protocol          = dmz_rule.protocol
          from_port         = dmz_rule.from_port
          to_port           = dmz_rule.to_port
          cidr_blocks       = dmz_rule.cidr_blocks
        }
      ]
    ]
  )
}

resource "aws_security_group_rule" "dmz" {
  for_each  = { for entry in local.dmz_security_group_ruleset: "${entry.security_group_id}.${entry.type}.${entry.protocol}.${entry.from_port}.${entry.to_port}.${entry.cidr_blocks[0]}" => entry }
    security_group_id = each.value.security_group_id
    description       = each.value.description
    type              = each.value.type
    protocol          = each.value.protocol
    from_port         = each.value.from_port
    to_port           = each.value.to_port
    cidr_blocks       = each.value.cidr_blocks
}
