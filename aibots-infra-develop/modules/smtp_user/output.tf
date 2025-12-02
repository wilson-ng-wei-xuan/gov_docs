output "smtp_user"{
  value = aws_iam_user.smtp_user
  description = <<-EOT
    The IAM user with ses access.
    Read more: [aws_iam_user](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_user)
  EOT
}

output "lambda_function" {
  value = var.secret_rotation_schedule_expression == null ? null : aws_lambda_function.smtp_user
  description = <<-EOT
    The lambda function.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
  EOT
}

output "lambda_role" {
  value = var.secret_rotation_schedule_expression == null ? null : aws_iam_role.smtp_user
  description = <<-EOT
    The iam role for the deployed lambda.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role
  EOT
}

output "cloudwatch_log_group" {
  value = var.secret_rotation_schedule_expression == null ? null : module.cloudwatch_log_group.cloudwatch_log_group
  description = <<-EOT
    The cloudwatch logs for the deployed lambda.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group
  EOT
}