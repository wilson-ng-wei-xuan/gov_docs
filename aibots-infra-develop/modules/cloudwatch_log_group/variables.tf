##
## Cloudwatch specific variables
##
variable "name" {
  type        = string
  description = <<EOT
    The name of the log group.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group
  EOT
}

variable "retention_in_days" {
  type        = number
  default     = 365
  description = <<EOT
    (Optional) Specifies the number of days you want to retain log events in the specified log group.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group
  EOT
}

variable "destination_arn" {
  type        = string
  default     = null
  description = <<EOT
    The ARN of the destination to deliver matching log events to. Kinesis stream or Lambda function ARN.
    If not provided, the subscription filter will not be created.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_subscription_filter#destination_arn
  EOT
}

variable "filter_pattern" {
  type        = string
  default     = null
# I need to add some sort of validation here,
# if destination_arm is not null, this also cannot null.
# but terraform does not allow a validation to reference to another variable.
# so we just let the terraform fail the AWS validation.
  description = <<EOT
    CloudWatch Logs filter pattern for subscribing to a filtered stream of log events.
    You need to provide a pattern if destination_arn is not null. e.g.:
    filter_pattern = "?\"[NOTIFY]\" ?\"[ERROR]\" ?\"[WARNING]\" ?\"[WARN]\" ?\"[CRITICAL]\""
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_subscription_filter#filter_pattern
  EOT
}