######################################################################################
module "lambda" {
  source = "../modules/lambda"

  # The variables required by your module e.g shown below
  function_name = "${var.project_code}-${var.project_desc}"
  memory_size = 128
  # security_group_ids = []
  # subnet_ids = []
  security_group_ids = [ data.aws_security_group.aibots_ez["${local.secgrp_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id ]
  # subnet_ids = [ data.aws_subnet.aibots_ez["${local.subnet_prefix}-${local.az_deployment}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]
  subnet_ids = [ data.aws_subnet.aibots_ez["${local.subnet_prefix}-a-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
                data.aws_subnet.aibots_ez["${local.subnet_prefix}-b-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]

  filename= "${path.module}/source/lambda/project.zip"
  handler = "lambda_function.lambda_handler"
  timeout = var.timeout

  runtime = local.default_lambda_runtime
  layers = [ data.aws_lambda_layer_version.LambdaInsightsExtension.id,
             data.aws_lambda_layer_version.requests-aws4auth.id ]

  managed_policy_arns = [ "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole" ]

  environment_variables = {
    # SQS_FANOUT__URL = module.sqs_fanout.sqs_queue.url
    # PROJECT__BUCKET = local.APPRAISER_PROJECT__BUCKET
    # # this is where the batch xlsx are dropped
    # APPRAISER_BATCH_UPLOAD__PATH = local.APPRAISER_BATCH_UPLOAD__PATH
    # APPRAISER_BATCH_UPLOAD__FILE_EXT = local.APPRAISER_BATCH_UPLOAD__FILE_EXT # this is the trigger to batch gen appr
    # # this is where the generated appr are dropped
    # APPRAISER_BATCH_GEN_APPR__PATH = local.APPRAISER_BATCH_GEN_APPR__PATH
    # APPRAISER_BATCH_GEN_APPR__FILE_EXT = local.APPRAISER_BATCH_GEN_APPR__FILE_EXT # place holder, not used at the moment.
    # # this is where the zipped appr are dropped
    # APPRAISER_BATCH_ZIPPED_APPR__PATH = local.APPRAISER_BATCH_ZIPPED_APPR__PATH
    # APPRAISER_BATCH_ZIPPED_APPR__FILE_EXT = local.APPRAISER_BATCH_ZIPPED_APPR__FILE_EXT # this is the trigger to ses
    # # this is where the job is atchived after sent
    # APPRAISER_BATCH_ARCHIVE__PATH = local.APPRAISER_BATCH_ARCHIVE__PATH
    # APPRAISER_BATCH_ARCHIVE__FILE_EXT = local.APPRAISER_BATCH_ARCHIVE__FILE_EXT # place holder, not used
    # APPRAISER_MAIN_API__PTE_URL = local.APPRAISER_MAIN_API__PTE_URL
    # # This is the sendemail API
    # EMAIL_SMTP_API__PTE_URL= local.SHAREDSVC_EMAIL-SEND-PTE__URL
    # EMAIL_SMTP_ACCESS = local.APPRAISER_EMAIL-SMTP__PARAM
    # EMAIL_SMTP_ATTACHMENT_BUCKET = local.SHAREDSVC_EMAIL__BUCKET
    # EMAIL_SMTP_ATTACHMENT_PATH = "${var.project_code}/"
  }


  inline_policy = [
    {
      name = "AllowPermissions"
      policy = jsonencode(
        {
          Version = "2012-10-17",
          Statement = [
            {
              Action = [
                "aoss:ListCollections",
                "aoss:APIAccessAll"
              ],
              Resource = [
                "*"
              ]
              Effect = "Allow"
            },
            {
              Action = [
                "cloudwatch:GetMetricStatistics"
              ],
              Resource = [
                "*"
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