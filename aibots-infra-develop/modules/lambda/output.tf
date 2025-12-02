output "cloudwatch_log_group" {
  value = module.cloudwatch_log_group.cloudwatch_log_group
  description = <<-EOT
    The cloudwatch logs for the deployed lambda.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group
  EOT
}

output "iam_role" {
  value = aws_iam_role.lambda_role
  description = <<-EOT
    The iam role for the deployed lambda.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role
  EOT
}

output "lambda_function" {
  value = var.ignore_changes ? aws_lambda_function.simple_lambda_ignore_changes[0] : aws_lambda_function.simple_lambda[0]
  description = <<-EOT
    The lambda function.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
  EOT
}