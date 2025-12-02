resource "aws_secretsmanager_secret" "secretsmanager_secret" {
  name             = "${local.secret_name}"
  force_overwrite_replica_secret = false
  recovery_window_in_days        = 30

  tags = merge(
    { "Name" = "${local.kms_name}" },
    local.tags,
  )
}

variable "key_pair" {
  default = {
    ENCRYPT_API_TOKEN = "DEFAULT"
    ENCRYPT_ID        = "DEFAULT"
  }
  type = map(string)
}

resource "aws_secretsmanager_secret_version" "secretsmanager_secret" {
  lifecycle {
    ignore_changes = [
      secret_string,
    ]
  }

  secret_id     = aws_secretsmanager_secret.secretsmanager_secret.id
  secret_string = jsonencode(var.key_pair)
}

data "aws_secretsmanager_secret_version" "secretsmanager_secret" {
  depends_on = [aws_secretsmanager_secret_version.secretsmanager_secret]

  secret_id     = aws_secretsmanager_secret.secretsmanager_secret.id
  version_stage = "AWSCURRENT"
}