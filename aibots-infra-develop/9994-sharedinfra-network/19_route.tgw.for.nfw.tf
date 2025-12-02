module "route_tgw" {
  source = "../modules/route"

  route_table_id = local.route_table_tgw
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
      vpc_endpoint_id         = flatten(data.aws_networkfirewall_firewall.sharedinfra_ez.firewall_status[*].sync_states[*].*.attachment[*])[0].endpoint_id
    }
  ]

  tags = local.tags # route does not have tags, but this is to align all codes.
}