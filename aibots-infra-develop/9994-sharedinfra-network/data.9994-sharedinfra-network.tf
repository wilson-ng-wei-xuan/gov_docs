locals {
  cidr_management   = concat( data.aws_vpc.management_ez.cidr_block_associations.*.cidr_block )

  cidr_sharedinfra  = concat( data.aws_vpc.sharedinfra_ez.cidr_block_associations.*.cidr_block )

  cidr_projects     = concat( data.aws_vpc.sharedsvc_ez.cidr_block_associations.*.cidr_block,
                              data.aws_vpc.aibots_ez.cidr_block_associations.*.cidr_block, )

  cidr_all          = concat( data.aws_vpc.management_ez.cidr_block_associations.*.cidr_block,
                              data.aws_vpc.sharedinfra_ez.cidr_block_associations.*.cidr_block,
                              data.aws_vpc.sharedsvc_ez.cidr_block_associations.*.cidr_block,
                              data.aws_vpc.aibots_ez.cidr_block_associations.*.cidr_block, )

  subnet_cicd       = [ data.aws_subnet.management_ez["${local.subnet_prefix}-a-${terraform.workspace}ezcicd-management"].cidr_block,
                        data.aws_subnet.management_ez["${local.subnet_prefix}-b-${terraform.workspace}ezcicd-management"].cidr_block, ]

  subnet_test       = [ data.aws_subnet.management_ez["${local.subnet_prefix}-a-${terraform.workspace}eztest-management"].cidr_block,
                        data.aws_subnet.management_ez["${local.subnet_prefix}-b-${terraform.workspace}eztest-management"].cidr_block, ]

  subnet_ingress    = [ data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-a-${terraform.workspace}ezingress-sharedinfra"].cidr_block,
                        data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-b-${terraform.workspace}ezingress-sharedinfra"].cidr_block, ]

  subnet_dmz        = [ data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-a-${terraform.workspace}ezdmz-sharedinfra"].cidr_block,
                        data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-b-${terraform.workspace}ezdmz-sharedinfra"].cidr_block, ]

  subnet_egress     = [ data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-a-${terraform.workspace}ezegress-sharedinfra"].cidr_block,
                        data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-b-${terraform.workspace}ezegress-sharedinfra"].cidr_block, ]

  subnet_inspect    = [ data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-a-${terraform.workspace}ezinspect-sharedinfra"].cidr_block,
                        data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-b-${terraform.workspace}ezinspect-sharedinfra"].cidr_block, ]

  subnet_endpt      = [ data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-a-${terraform.workspace}ezendpt-sharedinfra"].cidr_block,
                        data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-b-${terraform.workspace}ezendpt-sharedinfra"].cidr_block, ]

  subnet_app        = [ data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-a-${terraform.workspace}ezapp-sharedsvc"].cidr_block,
                        data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-b-${terraform.workspace}ezapp-sharedsvc"].cidr_block,
                        data.aws_subnet.aibots_ez["${local.subnet_prefix}-a-${terraform.workspace}ezapp-aibots"].cidr_block,
                        data.aws_subnet.aibots_ez["${local.subnet_prefix}-b-${terraform.workspace}ezapp-aibots"].cidr_block, ]

  subnet_db         = [ data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-a-${terraform.workspace}ezdb-sharedsvc"].cidr_block,
                        data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-b-${terraform.workspace}ezdb-sharedsvc"].cidr_block,
                        data.aws_subnet.aibots_ez["${local.subnet_prefix}-a-${terraform.workspace}ezdb-aibots"].cidr_block,
                        data.aws_subnet.aibots_ez["${local.subnet_prefix}-b-${terraform.workspace}ezdb-aibots"].cidr_block, ]

  subnet_all = concat(local.subnet_cicd,
                      local.subnet_test,
                      local.subnet_ingress,
                      local.subnet_dmz,
                      local.subnet_egress,
                      local.subnet_inspect,
                      local.subnet_endpt,
                      local.subnet_app,
                      local.subnet_db, )

  route_table_cicd    = [ data.aws_route_table.management_ez["${local.routetable_prefix}-*-${terraform.workspace}ezcicd-management"].id, ]

  route_table_test    = [ data.aws_route_table.management_ez["${local.routetable_prefix}-*-${terraform.workspace}eztest-management"].id, ]

  route_table_ingress = [ data.aws_route_table.sharedinfra_ez["${local.routetable_prefix}-*-${terraform.workspace}ezingress-sharedinfra"].id, ]

  route_table_dmz     = [ data.aws_route_table.sharedinfra_ez["${local.routetable_prefix}-*-${terraform.workspace}ezdmz-sharedinfra"].id, ]

  route_table_egress  = [ data.aws_route_table.sharedinfra_ez["${local.routetable_prefix}-*-${terraform.workspace}ezegress-sharedinfra"].id, ]

  route_table_inspect = [ data.aws_route_table.sharedinfra_ez["${local.routetable_prefix}-*-${terraform.workspace}ezinspect-sharedinfra"].id, ]

  route_table_endpt   = [ data.aws_route_table.sharedinfra_ez["${local.routetable_prefix}-*-${terraform.workspace}ezendpt-sharedinfra"].id, ]

  route_table_app     = [ data.aws_route_table.sharedsvc_ez["${local.routetable_prefix}-*-${terraform.workspace}ezapp-sharedsvc"].id,
                          data.aws_route_table.aibots_ez["${local.routetable_prefix}-*-${terraform.workspace}ezapp-aibots"].id, ]

  route_table_db      = [ data.aws_route_table.sharedsvc_ez["${local.routetable_prefix}-*-${terraform.workspace}ezdb-sharedsvc"].id,
                          data.aws_route_table.aibots_ez["${local.routetable_prefix}-*-${terraform.workspace}ezdb-aibots"].id, ]

  route_table_tgw     = [ data.aws_route_table.sharedinfra_ez["${local.routetable_prefix}-*-${terraform.workspace}eztgw-sharedinfra"].id , ]

  route_table_all     = concat( local.route_table_cicd,
                                local.route_table_test,
                                local.route_table_ingress,
                                local.route_table_dmz,
                                local.route_table_egress,
                                local.route_table_inspect,
                                local.route_table_endpt,
                                local.route_table_app,
                                local.route_table_db, )

  nacl_cicd     = concat( data.aws_network_acls.management_ez_cicd.ids )

  nacl_test     = concat( data.aws_network_acls.management_ez_test.ids )

  nacl_ingress  = concat( data.aws_network_acls.sharedinfra_ez_ingress.ids )

  nacl_dmz      = concat( data.aws_network_acls.sharedinfra_ez_dmz.ids )

  nacl_egress   = concat( data.aws_network_acls.sharedinfra_ez_egress.ids )

  nacl_inspect  = concat( data.aws_network_acls.sharedinfra_ez_inspect.ids )

  nacl_endpt    = concat( data.aws_network_acls.sharedinfra_ez_endpt.ids )

  nacl_sharedsvc_app  = concat( data.aws_network_acls.sharedsvc_ez_app.ids )
  nacl_aibots_app  = concat( data.aws_network_acls.aibots_ez_app.ids )

  nacl_sharedsvc_db   = concat( data.aws_network_acls.sharedsvc_ez_db.ids )
  nacl_aibots_db   = concat( data.aws_network_acls.aibots_ez_db.ids )

  nacl_tgw      = concat( data.aws_network_acls.management_ez_tgw.ids,
                          data.aws_network_acls.sharedinfra_ez_tgw.ids,
                          data.aws_network_acls.sharedsvc_ez_tgw.ids,
                          data.aws_network_acls.aibots_ez_tgw.ids, )

  nacl_all  = concat( local.nacl_cicd,
                      local.nacl_test,
                      local.nacl_ingress,
                      local.nacl_dmz,
                      local.nacl_egress,
                      local.nacl_inspect,
                      local.nacl_endpt,
                      local.nacl_sharedsvc_app,
                      local.nacl_aibots_app,
                      local.nacl_sharedsvc_db,
                      local.nacl_aibots_db, )
  }

# locals{
#   project_cidr_block_associations = concat(
#     data.aws_vpc.sharedsvc_ez.cidr_block_associations,
#     data.aws_vpc.aibots_ez.cidr_block_associations,
#   )

#   project_cidr_blocks = flatten(
#     [for index in range( length( local.project_cidr_block_associations ) ) :
#       local.project_cidr_block_associations[index].cidr_block
#     ]
#   )
# }
