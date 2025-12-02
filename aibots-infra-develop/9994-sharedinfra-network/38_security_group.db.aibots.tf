locals {
  # aibots_ez_db_security_group_ids = concat( data.aws_security_group.aibots_ez_db.*.id, )
  aibots_ez_db_security_group_ids = concat( [ data.aws_security_group.aibots_ez["${local.secgrp_prefix}-${terraform.workspace}ezdb-aibots"].id ], )

  aibots_ez_db_security_group_rules = [
    # {
    #   description     = "Allow inbound Mongo tcp 27017 from cicd."
    #   type            = "ingress"
    #   protocol        = "tcp"
    #   from_port       = 27017
    #   to_port         = 27017
    #   cidr_blocks     = [ data.aws_subnet.management_ez["${local.subnet_prefix}-a-${terraform.workspace}ezcicd-management"].cidr_block ,
    #                       data.aws_subnet.management_ez["${local.subnet_prefix}-b-${terraform.workspace}ezcicd-management"].cidr_block , ]
    # },
    {
      description     = "Allow inbound Mongo tcp 27017 from test."
      type            = "ingress"
      protocol        = "tcp"
      from_port       = 27017
      to_port         = 27017
      cidr_blocks     = [ data.aws_subnet.management_ez["${local.subnet_prefix}-a-${terraform.workspace}eztest-management"].cidr_block ,
                          data.aws_subnet.management_ez["${local.subnet_prefix}-b-${terraform.workspace}eztest-management"].cidr_block , ]
    },
    {
      description     = "Allow inbound Mongo tcp 27017 from app."
      type            = "ingress"
      protocol        = "tcp"
      from_port       = 27017
      to_port         = 27017
      cidr_blocks     = [ data.aws_subnet.aibots_ez["${local.subnet_prefix}-a-${terraform.workspace}ezapp-aibots"].cidr_block ,
                          data.aws_subnet.aibots_ez["${local.subnet_prefix}-b-${terraform.workspace}ezapp-aibots"].cidr_block , ]
    },
    {
      description     = "Allow inbound Opensearch tcp 443 from app."
      type            = "ingress"
      protocol        = "tcp"
      from_port       = 443
      to_port         = 443
      cidr_blocks     = [ data.aws_subnet.aibots_ez["${local.subnet_prefix}-a-${terraform.workspace}ezapp-aibots"].cidr_block ,
                          data.aws_subnet.aibots_ez["${local.subnet_prefix}-b-${terraform.workspace}ezapp-aibots"].cidr_block , ]
    },
    # Not needed as secret rotator is using the control plane (boto3) to modify the password
    # {
    #   description     = "Allow inbound Mongo tcp 27017 from secret rotator."
    #   type            = "ingress"
    #   protocol        = "tcp"
    #   from_port       = 27017
    #   to_port         = 27017
    #   cidr_blocks     = [ data.aws_subnet.aibots_ez["${local.subnet_prefix}-a-${terraform.workspace}ezdb-aibots"].cidr_block ,
    #                       data.aws_subnet.aibots_ez["${local.subnet_prefix}-b-${terraform.workspace}ezdb-aibots"].cidr_block , ]
    # },
    # {
    #   description     = "Allow outbound Mongo tcp 27017 from secret rotator."
    #   type            = "egress"
    #   protocol        = "tcp"
    #   from_port       = 27017
    #   to_port         = 27017
    #   cidr_blocks     = [ data.aws_subnet.aibots_ez["${local.subnet_prefix}-a-${terraform.workspace}ezdb-aibots"].cidr_block ,
    #                       data.aws_subnet.aibots_ez["${local.subnet_prefix}-b-${terraform.workspace}ezdb-aibots"].cidr_block , ]
    # },
    {
      description     = "Allow outbound tcp 443 to endpt."
      type            = "egress"
      protocol        = "tcp"
      from_port       = 443
      to_port         = 443
      cidr_blocks     = local.subnet_endpt
    },
  ]

  aibots_ez_db_security_group_ruleset = distinct(
    flatten(
      [for db_rule in local.aibots_ez_db_security_group_rules :
        [for index in range( length( local.aibots_ez_db_security_group_ids ) ) :
          {
            security_group_id = local.aibots_ez_db_security_group_ids[ index ]
            description       = db_rule.description
            type              = db_rule.type
            protocol          = db_rule.protocol
            from_port         = db_rule.from_port
            to_port           = db_rule.to_port
            cidr_blocks       = db_rule.cidr_blocks
          }
        ]
      ]
    )
  )
}

resource "aws_security_group_rule" "aibots_ez_db" {
  for_each  = { for entry in local.aibots_ez_db_security_group_ruleset: "${entry.security_group_id}.${entry.type}.${entry.protocol}.${entry.from_port}.${entry.to_port}.${entry.cidr_blocks[0]}" => entry }
    security_group_id = each.value.security_group_id
    description       = each.value.description
    type              = each.value.type
    protocol          = each.value.protocol
    from_port         = each.value.from_port
    to_port           = each.value.to_port
    cidr_blocks       = each.value.cidr_blocks
}
