module "route_cicd" {
  source = "../modules/route"

  route_table_id = local.route_table_cicd

  # transit_gateway_id = data.aws_ec2_transit_gateway.sharedinfra_ez.id
  # tgw_destination_cidr_block = concat(
  #   # REPLACE this local.subnet_XXX according to this deployment
  #   local.subnet_app, # app tier need this to talk to each other
  # ) 

  additional_routes = [
    { #Internet to use management IGW
      destination_cidr_block  = "0.0.0.0/0"
      gateway_id              = data.aws_internet_gateway.management_ez.id
    },
    ############################################################################
    # # SIT we allow connection to the workload.
    ############################################################################
    { # SIT GCC range to use TGW
      destination_cidr_block  = "100.95.107.0/26"
      transit_gateway_id      = data.aws_ec2_transit_gateway.sharedinfra_ez.id
    },
    { # SIT GCC range to use TGW
      destination_cidr_block  = "100.126.166.0/24"
      transit_gateway_id      = data.aws_ec2_transit_gateway.sharedinfra_ez.id
    },
    { # SIT Internal range to use TGW
      destination_cidr_block  = "172.29.0.0/16"
      transit_gateway_id      = data.aws_ec2_transit_gateway.sharedinfra_ez.id
    },
    # ##########################################################################
    # # remark these to disable connection to the workload.
    # ##########################################################################
    # { # UAT GCC range to use TGW
    #   destination_cidr_block  = "100.94.133.128/25"
    #   transit_gateway_id      = data.aws_ec2_transit_gateway.sharedinfra_ez.id
    # },
    # { # UAT GCC range to use TGW
    #   destination_cidr_block  = "100.124.98.0/24"
    #   transit_gateway_id      = data.aws_ec2_transit_gateway.sharedinfra_ez.id
    # },
    # { # UAT Internal range to use TGW
    #   destination_cidr_block  = "172.30.0.0/16"
    #   transit_gateway_id      = data.aws_ec2_transit_gateway.sharedinfra_ez.id
    # },
    # ##########################################################################
    # # remark these to disable connection to the workload.
    # ##########################################################################
    # { # PRD GCC range to use TGW
    #   destination_cidr_block  = "100.93.230.128/25"
    #   transit_gateway_id      = data.aws_ec2_transit_gateway.sharedinfra_ez.id
    # },
    # { # PRD GCC range to use TGW
    #   destination_cidr_block  = "100.123.82.0/24"
    #   transit_gateway_id      = data.aws_ec2_transit_gateway.sharedinfra_ez.id
    # },
    # { # PRD Internal range to use TGW
    #   destination_cidr_block  = "172.31.0.0/16"
    #   transit_gateway_id      = data.aws_ec2_transit_gateway.sharedinfra_ez.id
    # },
  ]

  tags = local.tags # route does not have tags, but this is to align all codes.
}
