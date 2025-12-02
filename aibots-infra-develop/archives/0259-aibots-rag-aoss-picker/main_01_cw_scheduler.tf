resource "aws_cloudwatch_event_rule" "schedule" {
  name        = "${local.cwevent_name}"
  description = "invoke lambda ${module.lambda.lambda_function.function_name}"
  schedule_expression = var.schedule

  tags = local.tags
}

resource "aws_cloudwatch_event_target" "schedule_lambda" {
  rule = aws_cloudwatch_event_rule.schedule.name
  target_id = "processing_lambda"
  arn = "${module.lambda.lambda_function.arn}"

  input = jsonencode(
    {
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
  )
}

resource "aws_lambda_permission" "allow_cloudwatch_event_rule_to_run_lambda" {
  statement_id  = "AllowExecutionFromCloudWatchEvent"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda.lambda_function.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}