resource "aws_cloudwatch_log_group" "cloudwatch_log_group" {
  name				= local.cw_log_group_name
  retention_in_days	= var.retention_in_days
  tags = merge(
    { "Name"= local.cw_log_group_name },
    local.tags
  )
}
