resource "aws_route" "this" {
  for_each  = { for entry in local.route_entry: "${ entry.route_table_id }.${ entry.destination_cidr_block }" => entry }
    route_table_id          = each.value.route_table_id
    destination_cidr_block  = each.value.destination_cidr_block

    carrier_gateway_id        = try(each.value.carrier_gateway_id, null)
    core_network_arn          = try(each.value.core_network_arn, null)
    egress_only_gateway_id    = try(each.value.egress_only_gateway_id, null)
    gateway_id                = try(each.value.gateway_id, null)
    local_gateway_id          = try(each.value.local_gateway_id, null)
    nat_gateway_id            = try(each.value.nat_gateway_id, null)
    network_interface_id      = try(each.value.network_interface_id, null)
    transit_gateway_id        = try(each.value.transit_gateway_id, null)
    vpc_endpoint_id           = try(each.value.vpc_endpoint_id, null)
    vpc_peering_connection_id = try(each.value.vpc_peering_connection_id, null)
}

locals {
  route_to_tgw_set = var.transit_gateway_id == null ? [] : distinct(
    flatten(
      [for index in range( length( var.tgw_destination_cidr_block ) ) :
        {
          destination_cidr_block  = var.tgw_destination_cidr_block[ index ]
          transit_gateway_id      = var.transit_gateway_id
        }
      ]
    )
  )

  route_set = concat(
    local.route_to_tgw_set,
    # ADD extra routes, e.g. igw, nat here
    var.additional_routes,
  )

  route_entry = distinct(
    flatten(
      [for route in local.route_set :
        # REPLACE this local.route_table_XXX according to this deployment
        [for index in range( length( var.route_table_id ) ) :
          {
            route_table_id            = var.route_table_id[ index ]
            destination_cidr_block    = route.destination_cidr_block

            carrier_gateway_id        = try(route.carrier_gateway_id, null)
            core_network_arn          = try(route.core_network_arn, null)
            egress_only_gateway_id    = try(route.egress_only_gateway_id, null)
            gateway_id                = try(route.gateway_id, null)
            local_gateway_id          = try(route.local_gateway_id, null)
            nat_gateway_id            = try(route.nat_gateway_id, null)
            network_interface_id      = try(route.network_interface_id, null)
            transit_gateway_id        = try(route.transit_gateway_id, null)
            vpc_endpoint_id           = try(route.vpc_endpoint_id, null)
            vpc_peering_connection_id = try(route.vpc_peering_connection_id, null)
          }
        ]
      ]
    )
  )
}