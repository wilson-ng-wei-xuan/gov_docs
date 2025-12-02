locals {
    # today       = timestamp()
    today_local = formatdate("YYYY-MM-DD hh:mm:ss", timeadd( timestamp(), "8h") )
}

resource "tls_private_key" "project" {
  count = var.secret_rotation == false ? 0 : 1

  algorithm     = "RSA"
  rsa_bits      = 2048
}
# tls_private_key.project[0].public_key_pem   # goes to the CloudFront console → Key Management → Public Keys -> Create public key
# tls_private_key.project[0].private_key_pem  # use by Python code

resource "aws_secretsmanager_secret" "project" {
  count = var.secret_rotation == false ? 0 : 1

  name             = "${local.secret_name}-${var.project_desc}"
  description      = "The cloudfront PEM key ${var.project_code}-${var.project_desc}"
  force_overwrite_replica_secret = false
  recovery_window_in_days        = 7

  tags = merge(
    { "Name" = "${local.secret_name}-${var.project_desc}" },
    local.tags,
  )
}

resource "aws_secretsmanager_secret_version" "project" {
  count = var.secret_rotation == false ? 0 : 1

  lifecycle {
    ignore_changes = [
      secret_string,
      version_stages,
    ]
  }

  secret_id     = aws_secretsmanager_secret.project[0].id
  secret_string = tls_private_key.project[0].private_key_pem
  # secret_string = jsonencode( {
  #   "JWT": random_password.project[0].result
  # } )
}

resource "aws_secretsmanager_secret_rotation" "project" {
  count = var.secret_rotation == false ? 0 : 1

  secret_id           = aws_secretsmanager_secret.project[0].id
  rotation_lambda_arn = module.simple_lambda[0].lambda_function.arn

  rotation_rules {
    schedule_expression = var.secret_rotation_schedule_expression
    duration = "1h"
  }
}