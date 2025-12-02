resource "aws_cloudwatch_event_rule" "schedule" {
  for_each  = { for entry in var.schedule: "${entry.name}" => entry }

  name        = "${local.cwevent_name}-${each.value.name}"
  description = "invoke lambda ${module.lambda.lambda_function.function_name} by ${each.value.name}"
  schedule_expression = each.value.frequency

  tags = local.tags
}

resource "aws_cloudwatch_event_target" "schedule_lambda" {
  for_each  = { for entry in var.schedule: "${entry.name}" => entry }

  rule = aws_cloudwatch_event_rule.schedule[each.value.name].name
  target_id = "processing_lambda"
  arn = "${module.lambda.lambda_function.arn}"

  input = jsonencode(
    {
      SCHEDULE__BUCKET = local.SHAREDSVC_SCHEDULER__BUCKET
      SCHEDULE__PATH   = "schedule/${each.value.name}/"
    }
  )
}

resource "aws_lambda_permission" "allow_cloudwatch_event_rule_to_run_lambda" {
  for_each  = { for entry in var.schedule: "${entry.name}" => entry }

  statement_id  = "AllowExecutionFromCloudWatchEventBy${each.value.name}"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda.lambda_function.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule[each.value.name].arn
}