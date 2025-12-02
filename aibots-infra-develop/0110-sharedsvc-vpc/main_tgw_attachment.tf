resource "aws_ec2_transit_gateway_vpc_attachment" "project" {
  subnet_ids         = data.aws_subnets.project["tgw"].ids
  transit_gateway_id = data.aws_ec2_transit_gateway.sharedinfra_ez.id
  vpc_id             = local.vpc_id

  appliance_mode_support  = "disable"

  tags = merge(
    { "Name" = "${local.tgw_attach_name}" },
    local.tags
  )
}

# This default route is only if you deploy the IGW
resource "aws_ec2_transit_gateway_route" "default" {
  count = var.deploy_igw == true ? 1 : 0

  destination_cidr_block         = "0.0.0.0/0"
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.project.id
  transit_gateway_route_table_id = data.aws_ec2_transit_gateway.sharedinfra_ez.association_default_route_table_id
}

################################################################################
# create the vpc flow logs for the tgw_attachment created
################################################################################
resource "aws_flow_log" "tgw_attachment" {
  iam_role_arn                  = data.aws_iam_role.vpc-flow-logger.arn
  log_destination               = module.tgw_attachment.cloudwatch_log_group.arn
  traffic_type                  = "ALL"
  transit_gateway_attachment_id = aws_ec2_transit_gateway_vpc_attachment.project.id
  max_aggregation_interval      = 60 # must specify 60 for transit_gateway_id, transit_gateway_attachment_id
}

module "tgw_attachment" {
  source = "../modules/cloudwatch_log_group"

  name  = "/aws/vpc-flow-log/${local.tgw_attach_name}"

  retention_in_days	= "${var.retention_in_days}"
  # destination_arn = data.aws_lambda_function.slack_notification.arn # KIV until we know what to filter
  #  filter_pattern = "${var.filter_pattern}" # KIV until we know what to filter

  tags = merge(
    local.tags,
    { name = "/aws/vpc-flow-log/${local.tgw_attach_name}" }
  )
}