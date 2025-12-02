locals{
  # prefixlist_security_group_ids = concat( data.aws_security_group.sharedsvc_ez_app.*.id,
  #                                         data.aws_security_group.sharedsvc_ez_db.*.id, 
  #                                         data.aws_security_group.aibots_ez_app.*.id,
  #                                         data.aws_security_group.aibots_ez_db.*.id, )

  prefixlist_security_group_ids = concat( [ data.aws_security_group.sharedsvc_ez["${local.secgrp_prefix}-${terraform.workspace}ezapp-sharedsvc"].id ],
                                          [ data.aws_security_group.sharedsvc_ez["${local.secgrp_prefix}-${terraform.workspace}ezdb-sharedsvc"].id ],
                                          [ data.aws_security_group.aibots_ez["${local.secgrp_prefix}-${terraform.workspace}ezapp-aibots"].id ],
                                          [ data.aws_security_group.aibots_ez["${local.secgrp_prefix}-${terraform.workspace}ezdb-aibots"].id ], )
  # This is purposely not automated by pulling the
  # data "aws_vpc_endpoint" "gateway_endpoint"
  # {
  #   vpc_endpoint_type = Gateway 
  # }
  # because it is a single endpoint data:
  # - it will be complicate as you need to loop thru the list of gateway endpoints.
  # - the descritpion will not be able to customise
  prefixlist_security_group_rules = [
    {
      description     = "Allow outbound tcp 443 to s3 prefix list."
      type            = "egress"
      protocol        = "tcp"
      from_port       = 443
      to_port         = 443
      prefix_list_ids = [ "pl-6fa54006", ]
    },
    {
      description     = "Allow outbound tcp 443 to dynamodb prefix list."
      type            = "egress"
      protocol        = "tcp"
      from_port       = 443
      to_port         = 443
      prefix_list_ids = [ "pl-67a5400e", ]
    },
  ]

  # refer to 00_default_security_group.tf for the list of
  # >> local.prefixlist_security_group_rules
  prefixlist_security_group_ruleset = flatten(
    [for rules in local.prefixlist_security_group_rules :
      [for index in range( length( local.prefixlist_security_group_ids ) ) :
        {
          security_group_id = local.prefixlist_security_group_ids[ index ]
          description       = rules.description
          type              = rules.type
          protocol          = rules.protocol
          from_port         = rules.from_port
          to_port           = rules.to_port
          prefix_list_ids   = rules.prefix_list_ids
        }
      ]
    ]
  )
}

resource "aws_security_group_rule" "prefixlist" {
  for_each  = { for entry in local.prefixlist_security_group_ruleset: "${entry.security_group_id}.${entry.type}.${entry.protocol}.${entry.from_port}.${entry.to_port}.${entry.prefix_list_ids[0]}" => entry }
    security_group_id = each.value.security_group_id
    description       = each.value.description
    type              = each.value.type
    protocol          = each.value.protocol
    from_port         = each.value.from_port
    to_port           = each.value.to_port
    prefix_list_ids   = each.value.prefix_list_ids
}
