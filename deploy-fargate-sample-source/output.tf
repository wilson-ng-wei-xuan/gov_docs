output ecr_repo {
  value = aws_ecr_repository.ecr_repository.repository_url
}

output fqdn {
  value = "https://${var.lb_listener_rule_host_header[0]}/${var.project_code}"
}

output secrets {
  value = aws_secretsmanager_secret.secretsmanager_secret.name
}
