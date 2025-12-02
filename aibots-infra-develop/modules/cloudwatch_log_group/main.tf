resource "aws_cloudwatch_log_group" "cloudwatch_log_group" {
    #checkov:skip=CKV_AWS_158: "Ensure that CloudWatch Log Group is encrypted by KMS"
    
  name  = "${var.name}"
  retention_in_days	= "${var.retention_in_days}"

  tags = merge(
    { "Name" = "${var.name}" },
    local.tags,
    var.additional_tags
  )
}

resource "aws_cloudwatch_log_subscription_filter" "cloudwatch_log_group_logfilter" {
  count = var.destination_arn != null ? 1 : 0

  name            = "notification ${aws_cloudwatch_log_group.cloudwatch_log_group.name}"
  log_group_name  = aws_cloudwatch_log_group.cloudwatch_log_group.name
  filter_pattern  = var.filter_pattern
  destination_arn = var.destination_arn
}

################################################################################
# Central logs
################################################################################
data "aws_kinesis_firehose_delivery_stream" "central_logging" {
  name = "clm-central-logging-firehose"
}

data "aws_iam_role" "central_logging" {
  name = "central-logging-cloudwatch-firehose-role"
}

resource "aws_cloudwatch_log_subscription_filter" "central_logging" {
  name            = "central ${aws_cloudwatch_log_group.cloudwatch_log_group.name}"
  role_arn        = data.aws_iam_role.central_logging.arn
  log_group_name  = aws_cloudwatch_log_group.cloudwatch_log_group.name
  filter_pattern  = "" # log everything
  destination_arn = data.aws_kinesis_firehose_delivery_stream.central_logging.arn
  distribution    = "Random" # https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_subscription_filter#distribution
}