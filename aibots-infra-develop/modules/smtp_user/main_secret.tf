locals {
  smtp_user_name = "${local.tags.Project-Code}-${var.name}"
}

resource "aws_secretsmanager_secret" "smtp_user" {
  name             = "${local.secret_name}-${local.smtp_user_name}"
  description      = "The smtp_user ID PW ${local.smtp_user_name}"
  force_overwrite_replica_secret = false
  recovery_window_in_days        = 7

  tags = merge(
    { "Name" = "${local.secret_name}-${local.smtp_user_name}" },
    local.tags,
  )
}

resource "aws_secretsmanager_secret_version" "smtp_user" {
  lifecycle {
    ignore_changes = [
      secret_string,
      version_stages,
    ]
  }

  secret_id     = aws_secretsmanager_secret.smtp_user.id
  secret_string = jsonencode( {
    SMTP_FROM = "${var.from}@${var.domain}",
    SMTP_USER = aws_iam_access_key.smtp_user.id,
    SMTP_PASSWORD = aws_iam_access_key.smtp_user.ses_smtp_password_v4
  } )
}

resource "aws_secretsmanager_secret_rotation" "smtp_user" {
  secret_id           = aws_secretsmanager_secret.smtp_user.id
  rotation_lambda_arn = aws_lambda_function.smtp_user.arn

  rotation_rules {
    schedule_expression = var.secret_rotation_schedule_expression
    duration = "1h"
  }
}