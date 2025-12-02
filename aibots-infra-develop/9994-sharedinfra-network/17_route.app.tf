module "route_apps" {
  source = "../modules/route"

  route_table_id = local.route_table_app

  transit_gateway_id = data.aws_ec2_transit_gateway.sharedinfra_ez.id
  tgw_destination_cidr_block = concat(
    # REPLACE this local.subnet_XXX according to this deployment
    local.subnet_dmz,
    local.subnet_endpt,
    # local.subnet_inspect, # you don't specifically go to subnet_inspect as desitnation
  ) 

  additional_routes = [
    { # allow to internet
      # for ALB authentication, chatGPT, etc internet resources.
      # The NFW will be the access control on the allowed URL.
      destination_cidr_block  = "0.0.0.0/0"
      transit_gateway_id      = data.aws_ec2_transit_gateway.sharedinfra_ez.id
    }
  ]

  tags = local.tags # route does not have tags, but this is to align all codes.
}
