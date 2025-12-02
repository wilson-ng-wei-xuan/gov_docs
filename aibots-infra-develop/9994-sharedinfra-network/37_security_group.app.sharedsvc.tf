locals {
#  sharedsvc_ez_app_security_group_ids = concat( data.aws_security_group.sharedsvc_ez_app.*.id, )
  sharedsvc_ez_app_security_group_ids = concat( [ data.aws_security_group.sharedsvc_ez["${local.secgrp_prefix}-${terraform.workspace}ezapp-sharedsvc"].id ], )

  sharedsvc_ez_app_security_group_rules = [
################################################################################
# Allow inbound from ALB
################################################################################
    {
      description     = "Allow inbound tcp 443 from dmz."
      type            = "ingress"
      protocol        = "tcp"
      from_port       = 443
      to_port         = 443
      cidr_blocks     = local.subnet_dmz
    },
################################################################################
# LEON 2023/10/19 app coming in to sharedsvc
# Allow inbound from all app tier
# this is only applicable to sharedsvc
################################################################################
    {
      description     = "Allow inbound tcp 443 from application."
      type            = "ingress"
      protocol        = "tcp"
      from_port       = 443
      to_port         = 443
      cidr_blocks     = local.subnet_app
    },
################################################################################
# Allow outbound to internet
# routetable will route to NFW which will control the outbound access
################################################################################
    {
      description     = "Allow outbound tcp 443 to internet, NFW will traffic control."
      type            = "egress"
      protocol        = "tcp"
      from_port       = 443
      to_port         = 443
      cidr_blocks     = [ "0.0.0.0/0" ]
    },
    {
      description     = "Allow outbound tcp 587 to SMTP internet, NFW will traffic control."
      type            = "egress"
      protocol        = "tcp"
      from_port       = 587
      to_port         = 587
      cidr_blocks     = [ "0.0.0.0/0" ]
    },
################################################################################
# Allow outbound to mongo db.
################################################################################
    {
      description     = "Allow outbound tcp 27017 to Mongo db."
      type            = "egress"
      protocol        = "tcp"
      from_port       = 27017
      to_port         = 27017
      cidr_blocks     = [ data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-a-${terraform.workspace}ezdb-sharedsvc"].cidr_block,
                          data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-b-${terraform.workspace}ezdb-sharedsvc"].cidr_block, ]
    },
################################################################################
# Allow outbound to endpoints.
################################################################################
    {
      description     = "Allow outbound tcp 443 to endpt."
      type            = "egress"
      protocol        = "tcp"
      from_port       = 443
      to_port         = 443
      cidr_blocks     = local.subnet_endpt
    },
  ]

  sharedsvc_ez_app_security_group_ruleset = flatten(
    [for rules in local.sharedsvc_ez_app_security_group_rules :
      [for index in range( length( local.sharedsvc_ez_app_security_group_ids ) ) :
        {
          security_group_id = local.sharedsvc_ez_app_security_group_ids[ index ]
          description       = rules.description
          type              = rules.type
          protocol          = rules.protocol
          from_port         = rules.from_port
          to_port           = rules.to_port
          cidr_blocks       = rules.cidr_blocks
        }
      ]
    ]
  )
}

resource "aws_security_group_rule" "sharedsvc_ezapp" {
  for_each  = { for entry in local.sharedsvc_ez_app_security_group_ruleset: "${entry.security_group_id}.${entry.type}.${entry.protocol}.${entry.from_port}.${entry.to_port}.${entry.cidr_blocks[0]}" => entry }
    security_group_id = each.value.security_group_id
    description       = each.value.description
    type              = each.value.type
    protocol          = each.value.protocol
    from_port         = each.value.from_port
    to_port           = each.value.to_port
    cidr_blocks       = each.value.cidr_blocks
}
