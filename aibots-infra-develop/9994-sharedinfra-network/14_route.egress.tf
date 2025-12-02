module "route_egress" {
  source = "../modules/route"

  route_table_id = local.route_table_egress
  # transit_gateway_id = data.aws_ec2_transit_gateway.sharedinfra_ez.id
  # tgw_destination_cidr_block = concat(
  #   # REPLACE this local.subnet_XXX according to this deployment
  #   local.subnet_app,
  # ) 
  additional_routes = [
    {
      destination_cidr_block  = "0.0.0.0/0"
      gateway_id              = data.aws_internet_gateway.sharedinfra_ez.id
    },
    # allow app to talk to internet, NFW will block accordngly.
    {
      destination_cidr_block  = local.subnet_app[0] # sharedsvc
      vpc_endpoint_id         = flatten(data.aws_networkfirewall_firewall.sharedinfra_ez.firewall_status[*].sync_states[*].*.attachment[*])[0].endpoint_id
    },
    {
      destination_cidr_block  = local.subnet_app[1] # sharedsvc
      vpc_endpoint_id         = flatten(data.aws_networkfirewall_firewall.sharedinfra_ez.firewall_status[*].sync_states[*].*.attachment[*])[0].endpoint_id
    },
    {
      destination_cidr_block  = local.subnet_app[2] # aibots
      vpc_endpoint_id         = flatten(data.aws_networkfirewall_firewall.sharedinfra_ez.firewall_status[*].sync_states[*].*.attachment[*])[0].endpoint_id
    },
    {
      destination_cidr_block  = local.subnet_app[3] # aibots
      vpc_endpoint_id         = flatten(data.aws_networkfirewall_firewall.sharedinfra_ez.firewall_status[*].sync_states[*].*.attachment[*])[0].endpoint_id
    },
  ]

  tags = local.tags # route does not have tags, but this is to align all codes.
}
