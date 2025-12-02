resource "random_password" "project" {
  count = var.secret_rotation == false ? 0 : 1

  length  = 18
  special = true
  override_special = "_-"
  min_lower        = 1
  min_numeric      = 1
  min_special      = 1
  min_upper        = 1
}

resource "aws_secretsmanager_secret" "project" {
  count = var.secret_rotation == false ? 0 : 1

  name             = "${local.secret_name}-${var.project_desc}"
  description      = "The docdb ID PW ${var.project_code}-${var.project_desc}"
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
  secret_string = jsonencode( {
    "engine": "mongo",
    "host": "mongodb://${aws_docdbelastic_cluster.project.endpoint}:27017",
    "username": aws_docdbelastic_cluster.project.admin_user_name,
    "password": random_password.project[0].result,
    "ssl": true,
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