module "route_dmz" {
  source = "../modules/route"

  route_table_id = local.route_table_dmz

  transit_gateway_id = data.aws_ec2_transit_gateway.sharedinfra_ez.id
  tgw_destination_cidr_block = concat(
    # REPLACE this local.subnet_XXX according to this deployment
    local.subnet_app,
  )

  additional_routes = [
    { # allow to internet for ALB authentication.
      # The NFW will be the access control on the allowed URL.
      destination_cidr_block  = "0.0.0.0/0"
      transit_gateway_id      = data.aws_ec2_transit_gateway.sharedinfra_ez.id
    }
  ]

  tags = local.tags # route does not have tags, but this is to align all codes.
}