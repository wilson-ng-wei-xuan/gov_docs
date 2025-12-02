variable "name" {
  type        = string
  description = <<EOT
    (Required) The name of the ses user, e.g. . This will be used in the name of the iamuser.
  EOT
}

variable "domain" {
  type        = string
  description = <<EOT
    (Required) The @domain to restrict in the iampolicy.
  EOT
}

variable "from" {
  type        = string
  description = <<EOT
    (Required) The FROM sender, without the domain, to restrict in the iampolicy.
  EOT
}

variable "secret_rotation_schedule_expression" {
  type = string
  description = <<EOT
    The schedule to rotate secrets.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_rotation#schedule_expression
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

variable "layers" {
  type        = list(string)
  default     = []
  description = <<EOT
    (Optional) List of Lambda Layer Version ARNs (maximum of 5) to attach to your Lambda Function
    The LambdaInsightsExtension.id, e.g. [ data.aws_lambda_layer_version.LambdaInsightsExtension.id ]
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
  EOT
}

variable "destination_arn" {
  type = string
  default     = null
  description = <<EOT
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_subscription_filter
    The ARN of the destination to deliver matching log events to. Kinesis stream or Lambda function ARN.
    The lambda arn of the notification, e.g. data.aws_lambda_function.notification.arn
    If not provided, the subscription filter will not be created.
  EOT
}