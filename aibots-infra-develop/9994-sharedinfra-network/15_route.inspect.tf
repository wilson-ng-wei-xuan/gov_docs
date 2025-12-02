module "route_inspect" {
  source = "../modules/route"

  route_table_id = local.route_table_inspect
  transit_gateway_id = data.aws_ec2_transit_gateway.sharedinfra_ez.id
  tgw_destination_cidr_block = concat(
    # REPLACE this local.subnet_XXX according to this deployment
    # allow app to talk to internet, NFW will block accordngly.
    # [ local.subnet_app[0], # sharedsvc
    #   local.subnet_app[1], # sharedsvc
    #   local.subnet_app[2], # aibots
    #   local.subnet_app[3], # aibots
    # ]
    local.subnet_app
  ) 
  additional_routes = [
    {
      destination_cidr_block  = "0.0.0.0/0"
      nat_gateway_id          = data.aws_nat_gateway.sharedinfra_ez.id
    }
  ]

  tags = local.tags # route does not have tags, but this is to align all codes.
}
