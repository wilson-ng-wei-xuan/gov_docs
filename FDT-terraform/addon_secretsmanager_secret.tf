resource "aws_secretsmanager_secret" "secretsmanager_secret" {
  name             = "${local.kms_name}"
  force_overwrite_replica_secret = false
  recovery_window_in_days        = 30

  tags = merge(
    { "Name" = "${local.kms_name}" },
    local.context_tags,
  )
}

variable "key_pair" {
  default = {
    jwt_key             = "ALIGN WITH DAVID"
    couchbase_user      = "DEFAULT"
    couchbase_password  = "DEFAULT"
    couchbase_host      = "DEFAULT"
    qdrant_user         = "DEFAULT"
    qdrant_password     = "DEFAULT"
    qdrant_host         = "DEFAULT"
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