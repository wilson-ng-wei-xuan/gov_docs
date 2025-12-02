# resource "aws_sns_topic_policy" "default" {
#   arn    = aws_sns_topic.notification.arn
#   policy = data.aws_iam_policy_document.sns_topic_policy.json
# }

data "aws_iam_policy_document" "sns_topic_policy" {
  statement {
    effect  = "Allow"
    actions = ["SNS:Publish"]

    principals {
      type        = "AWS"
      identifiers = [ "*" ]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceOwner"
      values   = [ data.aws_caller_identity.current.account_id ]
    }

    resources = [aws_sns_topic.notification.arn]
  }
}

######################################################################################
module "simple_lambda" {
  source = "../modules/lambda"

  # The variables required by your module e.g shown below
  function_name = "${var.project_code}-${var.project_desc}"
  memory_size = 128
  # subnet_ids = [ data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-a-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
  #               data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-b-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]
  # subnet_ids = [ data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-${local.az_deployment}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]
  # security_group_ids = [ data.aws_security_group.sharedsvc_ez["${local.secgrp_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id ]
  subnet_ids  = []
  security_group_ids  = []
  filename= "${path.root}/source/lambda/${var.project_desc}.zip" # original working
  handler = "lambda_function.lambda_handler"
  timeout = 10

  runtime = local.default_lambda_runtime
  layers = [ data.aws_lambda_layer_version.LambdaInsightsExtension.id ]

  environment_variables = {
    DEFAULT_NOTIFICATION = aws_ssm_parameter.notification.id
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
                "sqs:ChangeMessageVisibility",
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes",
                "sqs:ReceiveMessage",
                "ssm:GetParameter"
              ],
              Resource = [
                # all DLQ can trigger this lambda
                "arn:aws:sqs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${local.sqs_prefix}-${terraform.workspace}*-dlq",
                # data.aws_ssm_parameter.sharedsvc-notification.arn,
                "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${local.para_store_prefix}-${terraform.workspace}ez-*-notification-default",
                "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${local.para_store_prefix}-${terraform.workspace}ez-*-notification",
              ]
              Effect = "Allow"
            },
          ]
        }
      )
    },
  ]

  retention_in_days = var.retention_in_days
  # You cannot ownself subscribe to ownself, with this error.
  # │ Error: putting CloudWatch Logs Subscription Filter (/aws/lambda/lambda-uatezapp-sharedsvc-notification): InvalidParameterException: The log group provided is reserved for the function logs of the destination function.
  # destination_arn = module.simple_lambda.lambda_function.arn

  tags = local.tags
}

################################################################################
# allows this SNS to trigger
resource "aws_sns_topic" "notification" {
  name = "${local.sns_name}"
  kms_master_key_id = "alias/aws/sns"

  application_failure_feedback_role_arn    = data.aws_iam_role.sns-delivery.arn
  application_success_feedback_role_arn    = data.aws_iam_role.sns-delivery.arn
  application_success_feedback_sample_rate = 100

  firehose_failure_feedback_role_arn       = data.aws_iam_role.sns-delivery.arn
  firehose_success_feedback_role_arn       = data.aws_iam_role.sns-delivery.arn
  firehose_success_feedback_sample_rate    = 100

  http_failure_feedback_role_arn           = data.aws_iam_role.sns-delivery.arn
  http_success_feedback_role_arn           = data.aws_iam_role.sns-delivery.arn
  http_success_feedback_sample_rate        = 100

  lambda_failure_feedback_role_arn         = data.aws_iam_role.sns-delivery.arn
  lambda_success_feedback_role_arn         = data.aws_iam_role.sns-delivery.arn
  lambda_success_feedback_sample_rate      = 100

  sqs_failure_feedback_role_arn            = data.aws_iam_role.sns-delivery.arn
  sqs_success_feedback_role_arn            = data.aws_iam_role.sns-delivery.arn
  sqs_success_feedback_sample_rate         = 100

  tags = merge(
    { "Name" = "${local.sns_name}" },
    local.tags
  )
}

resource "aws_lambda_permission" "with_sns" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = "${module.simple_lambda.lambda_function.arn}"
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.notification.arn
}

resource "aws_sns_topic_subscription" "notification" {
  topic_arn = aws_sns_topic.notification.arn
  protocol  = "lambda"
  endpoint  = module.simple_lambda.lambda_function.arn
}

################################################################################
# allows any cloudwatch logs subscription filter to trigger
resource "aws_lambda_permission" "logging" {
  statement_id  = "AllowExecutionFromCWLogGroup"
  action        = "lambda:InvokeFunction"
  function_name = "${module.simple_lambda.lambda_function.arn}"
  principal     = "logs.${data.aws_region.current.name}.amazonaws.com"
  source_arn    = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:*"
}

################################################################################
# allows any cloudwatch event to trigger
resource "aws_lambda_permission" "cloudwatch_event" {
  statement_id  = "AllowExecutionFromCWEvent"
  action        = "lambda:InvokeFunction"
  function_name = "${module.simple_lambda.lambda_function.arn}"
  principal     = "events.amazonaws.com"
  source_arn    = "arn:aws:events:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:rule/*"
}
