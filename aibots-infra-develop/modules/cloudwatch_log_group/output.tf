output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.cloudwatch_log_group
  description = <<-EOT
    The cloudwatch logs for the deployed lambda.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group
  EOT
}