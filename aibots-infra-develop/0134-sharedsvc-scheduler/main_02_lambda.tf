######################################################################################
module "lambda" {
  source = "../modules/lambda"

  # The variables required by your module e.g shown below
  function_name = "${var.project_code}-${var.project_desc}"
  memory_size = 128
  security_group_ids = [ data.aws_security_group.sharedsvc_ez["${local.secgrp_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id ]
  # subnet_ids = [ data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-${local.az_deployment}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]
  subnet_ids = [ data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-a-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
                 data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-b-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]

  filename= "${path.module}/source/lambda/helloworld.zip"
  handler = "lambda_function.lambda_handler"
  timeout = var.timeout

  runtime = local.default_lambda_runtime
  layers = [ data.aws_lambda_layer_version.LambdaInsightsExtension.id ]

  managed_policy_arns = [ "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole" ]

  environment_variables = {}


  inline_policy = [
    {
      name = "AllowPermissions"
      policy = jsonencode(
        {
          Version = "2012-10-17",
          Statement = [
            {
              Action = [
                "s3:ListBucket",
                "s3:GetObject",
              ],
              Resource = [
                data.aws_s3_bucket.scheduler.arn,
                "${data.aws_s3_bucket.scheduler.arn}/schedule/*",
              ]
              Effect = "Allow"
            },
            {
              Action = [
                "sqs:sendmessage",
              ],
              Resource = [
                "arn:aws:sqs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${local.sqs_prefix}-${terraform.workspace}${var.zone}${var.tier}-aibots-*"
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