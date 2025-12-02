module "route_dbs" {
  source = "../modules/route"

  route_table_id = local.route_table_db
  transit_gateway_id = data.aws_ec2_transit_gateway.sharedinfra_ez.id
  tgw_destination_cidr_block = concat(
    # REPLACE this local.subnet_XXX according to this deployment
    # local.subnet_cicd,
    local.subnet_test,
    local.subnet_endpt,
  ) 
  # additional_routes = [
  #   {
  #     destination_cidr_block  = "0.0.0.0/0"
  #     gateway_id              = data.aws_internet_gateway.sharedinfra_ez.id
  #   }
  # ]

  tags = local.tags # route does not have tags, but this is to align all codes.
}
