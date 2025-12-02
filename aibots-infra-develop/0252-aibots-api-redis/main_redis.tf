resource "aws_elasticache_serverless_cache" "redis" {
  engine = "redis"
  name   = local.redis_name
  description = "For API throttling"

  daily_snapshot_time      = "19:00"
  snapshot_retention_limit = var.snapshot_retention_limit

  # major_engine_version     = "7"
  security_group_ids       = [
    aws_security_group.project.id
  ]
  subnet_ids               = [
    data.aws_subnet.aibots_ez["${local.subnet_prefix}-a-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
    data.aws_subnet.aibots_ez["${local.subnet_prefix}-b-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
  ]

  tags = merge(
    local.tags,
    { "Name" = local.redis_name }
  )
}