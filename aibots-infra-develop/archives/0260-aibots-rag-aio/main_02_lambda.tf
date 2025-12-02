################################################################################
# use Template to render the variables in the env file
data "template_file" "env_var" {
  for_each  = { for entry in var.process: "${entry.name}" => entry }

  template  = file("${path.module}/source/lambda/${each.value.name}.env_var.json")
  # count       = length(var.pte_api)
  # template    = file("${path.module}/source/lambda/${var.pte_api[count.index].name}.environment.json")

  vars        = { # these are the variables to render
    ANALYTICS__BUCKET         = local.SHAREDSVC_ANALYTICS__BUCKET
    ANALYTICS__PATH           = var.project_code

    CLOUDFRONT__PUB_URL       = local.AIBOTS_CLOUDFRONT__PUB_URL
    CLOUDFRONT__BUCKET        = local.AIBOTS_CLOUDFRONT__BUCKET
    CLOUDFRONT__SECRET        = local.AIBOTS_CLOUDFRONT__SECRET
    CLOUDFRONT__PARAM         = local.AIBOTS_CLOUDFRONT__PARAM

    # PROJECT_RAG_AOSS__NAME    = local.AIBOTS_RAG_AOSS__NAME
    # PROJECT_RAG_AOSS__URL     = local.AIBOTS_RAG_AOSS__URL
    PROJECT_RAG_AOSS__PARAM   = local.AIBOTS_RAG_AOSS_PICKER__PARAM
    NOUS_API__PTE_URL         = local.SHAREDSVC_NOUS_API__PTE_URL
  }
}

################################################################################
# use Template to render the variables in the policy file
data "template_file" "policy" {
  for_each  = { for entry in var.process: "${entry.name}" => entry }

  template  = file("${path.module}/source/lambda/${each.value.name}.policy.json")
  # count       = length(var.pte_api)
  # template    = file("${path.module}/source/lambda/${var.pte_api[count.index].name}.policy.json")

  vars        = { # these are the variables to render
    PROJECT__BUCKET_ARN         = data.aws_s3_bucket.aibots.arn

    CLOUDFRONT__BUCKET_ARN      = data.aws_s3_bucket.aibots_cloudfront.arn
    CLOUDFRONT__SECRET_ARN      = data.aws_secretsmanager_secret.aibots_cloudfront.arn
    CLOUDFRONT__PARAM_ARN       = data.aws_ssm_parameter.aibots_cloudfront.arn

    PROJECT_RAG_AOSS__PARAM_ARN = data.aws_ssm_parameter.aibots_cloudfront.arn

    ANALYTICS__BUCKET_ARN       = data.aws_s3_bucket.analytics.arn
    SQS_SOURCE                  = module.sqs[each.value.name].sqs_queue.arn
    AWS_ID                      = data.aws_caller_identity.current.account_id
    AWS_REGION                  = data.aws_region.current.name
  }
}

################################################################################
module "lambda" {
  for_each  = { for entry in var.process: "${entry.name}" => entry }

  depends_on = [
    local.build_push_dkr_img
  ]

  source = "../modules/lambda"

  # The variables required by your module e.g shown below
  ignore_changes = true

  function_name = "${var.project_code}-${var.project_desc}-${each.value.name}"
  memory_size = 4096
  security_group_ids = [ data.aws_security_group.aibots_ez["${local.secgrp_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id ]
  # subnet_ids = [ data.aws_subnet.aibots_ez["${local.subnet_prefix}-${local.az_deployment}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]
  subnet_ids = [ data.aws_subnet.aibots_ez["${local.subnet_prefix}-a-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
                 data.aws_subnet.aibots_ez["${local.subnet_prefix}-b-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]

  filename = each.value.package_type == "Zip" ? "${path.module}/source/lambda/helloworld.zip" : null
  image_uri = each.value.package_type == "Image" ? "${aws_ecr_repository.project[ each.value.name ].repository_url}:latest" : null

  timeout = var.timeout

  handler = each.value.package_type == "Image" ? null : "lambda_function.lambda_handler"
  runtime = each.value.package_type == "Image" ? null : local.default_lambda_runtime
  layers  = each.value.package_type == "Image" ? null : [ data.aws_lambda_layer_version.LambdaInsightsExtension.id,
                                                          data.aws_lambda_layer_version.opensearch-py.id,
                                                          data.aws_lambda_layer_version.requests-aws4auth.id ]

  managed_policy_arns = [ "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole" ]

  # ##############################################################################
  # # If the lambdas are using the different set of env_vars, create the env_var json file and use this.
  # # you must un-comment the template above.
  # ##############################################################################
  environment_variables = jsondecode( data.template_file.env_var[ each.value.name ].rendered )
  #############################################################################
  # If ALL lambdas are using the same set of env_vars and you are lazy to create the env_var json file,
  # you can just use this for environment_variables
  # you must comment the template above.
  #############################################################################
  # environment_variables = {
  #   # SQS__URL = module.sqs.sqs_queue.url
  #   ANALYTICS__BUCKET = local.SHAREDSVC_ANALYTICS__BUCKET
  #   ANALYTICS__PATH = "${var.project_code}/"
  #   # This is the sendemail API
  #   # EMAIL_SMTP_API__PTE_URL = local.SHAREDSVC_EMAIL-SEND__PTE_URL
  #   # EMAIL_SMTP__SECRET = local.AIBOTS_EMAIL-SMTP__SECRET
  #   # EMAIL_SMTP_ATTACHMENT__BUCKET = local.SHAREDSVC_EMAIL__BUCKET
  #   # EMAIL_SMTP_ATTACHMENT__PATH = "${var.project_code}/"
  # }

  # ##############################################################################
  # # If the lambdas are using the different set of env_vars, create the env_var json file and use this.
  # ##############################################################################
  inline_policy = [
    {
      name = "AllowPermissions"
      policy = data.template_file.policy[ each.value.name ].rendered
    },
  ]
  ##############################################################################
  # # If ALL lambdas are using the same set of policy and you are lazy to create the policy json file,
  # # you can just use this for inline_policy
  ##############################################################################
  # inline_policy = [
  #   {
  #     name = "AllowPermissions"
  #     policy = jsonencode(
  #       {
  #         Version = "2012-10-17",
  #         Statement = [
  #           {
  #             Action = [
  #               "s3:ListBucket",
  #               "s3:GetObject",
  #       				"s3:PutObject",
  #               "sqs:ChangeMessageVisibility",
  #               "sqs:DeleteMessage",
  #               "sqs:GetQueueAttributes",
  #               "sqs:ReceiveMessage",
  #             ],
  #             Resource = [
  #               data.aws_s3_bucket.aibots.arn,
  #               "${data.aws_s3_bucket.aibots.arn}/*",
  #               data.aws_s3_bucket.analytics.arn,
  #               "${data.aws_s3_bucket.analytics.arn}/*",
  #               module.sqs[each.value.name].sqs_queue.arn
  #             ]
  #             Effect = "Allow"
  #           },
  #           {
  #             Action = [
  #       				"s3:DeleteObject",
  #             ],
  #             Resource = [
  #               data.aws_s3_bucket.aibots.arn,
  #               "${data.aws_s3_bucket.aibots.arn}/*",
  #             ]
  #             Effect = "Allow"
  #           },
  #         ]
  #       }
  #     )
  #   },
  # ]

  retention_in_days = var.retention_in_days
  destination_arn = data.aws_lambda_function.notification.arn

  tags = local.tags
}

# Event source from SQS
resource "aws_lambda_event_source_mapping" "project" {
  for_each  = { for entry in var.process: "${entry.name}" => entry }

  event_source_arn = module.sqs[each.value.name].sqs_queue.arn
  enabled          = true
  function_name    = module.lambda[each.value.name].lambda_function.arn
  # batch_size       = 1
}

# Event source from SQS-dlq
resource "aws_lambda_event_source_mapping" "project_dlq" {
  for_each  = { for entry in var.process: "${entry.name}" => entry }

  event_source_arn = module.sqs[each.value.name].sqs_queue_dlq.arn
  enabled          = true
  function_name    = data.aws_lambda_function.notification.arn
  # batch_size       = 1
}