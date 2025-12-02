######################################################################################
module "simple_lambda" {
  count = var.secret_rotation == false ? 0 : 1

  source = "../modules/lambda_secret_rotator_db_elastic"

  # # setting this has no effect as secret_rotator_cloudfront is hardcoded
  # The variables required by your module e.g shown below
  function_name = "${var.project_code}-secret-rotator-db"
  memory_size = 128
  security_group_ids = [ data.aws_security_group.aibots_ez["${local.secgrp_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id ]
  subnet_ids = [ data.aws_subnet.aibots_ez["${local.subnet_prefix}-a-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
                 data.aws_subnet.aibots_ez["${local.subnet_prefix}-b-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
  ]
  handler = "lambda_function.lambda_handler"
  timeout = 10
  runtime = local.default_lambda_runtime

  # # Only these are applicable
  layers = [ data.aws_lambda_layer_version.LambdaInsightsExtension.id ]
  secret_arn = aws_secretsmanager_secret.project[0].arn
  dbclusteridentifier = aws_docdbelastic_cluster.project.id
  retention_in_days = var.retention_in_days
  destination_arn = data.aws_lambda_function.notification.arn

  tags = local.tags
}