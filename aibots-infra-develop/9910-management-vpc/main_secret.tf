resource "random_password" "project" {
  count = var.secret_rotation == false ? 0 : 1

  length  = 64
  special = true
  override_special = "_-"
  min_lower        = 1
  min_numeric      = 1
  min_special      = 1
  min_upper        = 1
}

resource "aws_secretsmanager_secret" "project" {
  count = var.secret_rotation == false ? 0 : 1

  name             = "${local.secret_name}-project"
  force_overwrite_replica_secret = false
  recovery_window_in_days        = 7

  tags = merge(
    { "Name" = "${local.secret_name}-project" },
    local.tags,
  )
}

resource "aws_secretsmanager_secret_version" "project" {
  count = var.secret_rotation == false ? 0 : 1

  secret_id     = aws_secretsmanager_secret.project[0].id
  secret_string = jsonencode( {
    "JWT": random_password.project[0].result
  } )
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