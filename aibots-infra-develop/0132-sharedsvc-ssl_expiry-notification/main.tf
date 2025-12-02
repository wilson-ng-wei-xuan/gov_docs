resource "aws_cloudwatch_event_rule" "ssl_expiry" {
  name        = "${local.cwevent_name}"
  description = "To send notification on SSL expiry"

  tags = merge(
    { "Name" = "${local.cwevent_name}" },
    local.tags
  )

  event_pattern = jsonencode({
    source = ["aws.acm"],
    detail-type = ["ACM Certificate Approaching Expiration"]
  })
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.ssl_expiry.name
  target_id = "InvokeLambda"
  arn       = data.aws_lambda_function.notification.arn
}