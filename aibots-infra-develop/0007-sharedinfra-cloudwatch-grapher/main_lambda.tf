module "simple_lambda" {
  source = "../modules/lambda"

  # The variables required by your module e.g shown below
  function_name = "${var.project_code}-${var.project_desc}"
  memory_size = 256 # to half the time
  # subnet_ids = [ data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-a-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
  #               data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-b-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]
  # subnet_ids = [ data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-${local.az_deployment}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]
  # security_group_ids = [ data.aws_security_group.sharedsvc_ez["${local.secgrp_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id ]
  subnet_ids  = []
  security_group_ids  = []
  filename= "${path.module}/source/lambda/${var.project_desc}.zip"
  handler = "lambda_function.lambda_handler"
  timeout = 300

  runtime = local.default_lambda_runtime
  layers = [ data.aws_lambda_layer_version.LambdaInsightsExtension.id,
            data.aws_lambda_layer_version.pillow.arn, ]
            # data.aws_lambda_layer_version.pillow-Python311.arn, ]

  environment_variables = {
    START_DATE      = "",
    END_DATE        = "",
    LAMBDA_ARN      = "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:"
    EVENT_ROLE_ARN  = aws_iam_role.event_bridge.arn
    # START_DATE      = "2024-01-24T06:00:00.000Z",
    # END_DATE        = "2024-01-24T11:00:00.000Z",
  }

  managed_policy_arns = [
    # "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
  ]

  inline_policy = [
    {
      name = "AllowPermissions"
      policy = jsonencode(
        {
          Version = "2012-10-17",
          Statement = [
            {
              Action = [
                "cloudwatch:GetMetricWidgetImage",
                "cloudwatch:ListMetrics"
              ],
              Resource = [
                "*",
              ]
              Effect = "Allow"
            },
            {
              Action = [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "scheduler:CreateSchedule",
                "scheduler:DeleteSchedule",
                "iam:PassRole",
              ],
              Resource = [
                "${module.s3.bucket.arn}/*",
                "arn:aws:scheduler:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:schedule/*",
                aws_iam_role.event_bridge.arn
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