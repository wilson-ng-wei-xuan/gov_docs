################################################################################
# create the vpc flow logs for the subnets created
################################################################################
resource "aws_flow_log" "project" {
  for_each                 = { for entry in local.subnet : "${entry.tier}.${entry.az}" => entry }
  iam_role_arn             = data.aws_iam_role.vpc-flow-logger.arn
  log_destination          = module.project["${each.value.tier}.${each.value.az}"].cloudwatch_log_group.arn
  traffic_type             = "ALL"
  subnet_id                = aws_subnet.project["${each.value.tier}.${each.value.az}"].id
  max_aggregation_interval = 60
}

module "project" {
  source = "../modules/cloudwatch_log_group"

  for_each          = { for entry in local.subnet : "${entry.tier}.${entry.az}" => entry }
  name  = "/aws/vpc-flow-log/${local.subnet_prefix}-${each.value.az}-${terraform.workspace}${var.zone}${each.value.tier}-${var.project_code}"

  retention_in_days	= "${var.retention_in_days}"
  # destination_arn = data.aws_lambda_function.slack_notification.arn # KIV until we know what to filter
  # filter_pattern = "${var.filter_pattern}" # KIV until we know what to filter

  tags = merge(
    local.tags,
    { name = "/aws/vpc-flow-log/${local.subnet_prefix}-${each.value.az}-${terraform.workspace}${var.zone}${each.value.tier}-${var.project_code}" }
  )
}

################################################################################
# create the vpc flow logs as flagged by Security Hub
################################################################################
resource "aws_flow_log" "vpc" {
  count = var.vpc_cidr_block == null ? 0 : 1

  iam_role_arn             = data.aws_iam_role.vpc-flow-logger.arn
  log_destination          = module.vpc[count.index].cloudwatch_log_group.arn
  traffic_type             = "ALL"
  vpc_id                   = aws_vpc.project[count.index].id
  max_aggregation_interval = 60
}

module "vpc" {
  count = var.vpc_cidr_block == null ? 0 : 1

  source = "../modules/cloudwatch_log_group"

  name  = "/aws/vpc-flow-log/${local.vpc_name}"

  retention_in_days	= "${var.retention_in_days}"
  # destination_arn = data.aws_lambda_function.slack_notification.arn # KIV until we know what to filter
  # filter_pattern = "${var.filter_pattern}" # KIV until we know what to filter

  tags = merge(
    local.tags,
    { name = "/aws/vpc-flow-log/${local.vpc_name}" }
  )
}