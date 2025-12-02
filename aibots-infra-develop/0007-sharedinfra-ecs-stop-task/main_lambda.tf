######################################################################################
module "simple_lambda" {
  source = "../modules/lambda"

  # The variables required by your module e.g shown below
  function_name = "${var.project_code}-${var.project_desc}"
  memory_size = 128
  # security_group_ids = [ data.aws_security_group.sharedsvc_ez["${local.secgrp_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id ]
  security_group_ids = [ ]
  # subnet_ids = [ data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-${local.az_deployment}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]
  # subnet_ids = [ data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-a-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
  #               data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-b-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]
  subnet_ids = [ ]
  filename= "${path.module}/source/lambda/${var.project_desc}.zip"
  handler = "lambda_function.lambda_handler"
  timeout = 10

  runtime = local.default_lambda_runtime
  layers = [ data.aws_lambda_layer_version.LambdaInsightsExtension.id ]

  managed_policy_arns = [
    # "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
  ]

  inline_policy = [
    {
      name = "Permission"
      policy = jsonencode(
        {
          Version = "2012-10-17",
          Statement = [
            {
              Action = [
                "ecs:UpdateService",
              ],
              Resource = [
                "arn:aws:ecs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:service/${local.ecs_cluster_prefix}-${terraform.workspace}*/${local.ecs_service_prefix}-${terraform.workspace}*"
              ]
              Effect = "Allow"
            },
          ]
        }
      )
    },
  ]

  retention_in_days = var.retention_in_days
  destination_arn = data.aws_lambda_function.notification.arn

  tags = local.tags
}