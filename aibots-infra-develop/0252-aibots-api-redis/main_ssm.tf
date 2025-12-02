# data "aws_ssm_parameter" "whatever" {
#   name = aws_ssm_parameter.secret.name
# }
# # this is how you use it.
# resource "something" "name" {
#   "element_1" = jsondecode(data.aws_ssm_parameter.whatever.value)["key_1"]
#   "element_2" = jsondecode(data.aws_ssm_parameter.whatever.value)["key_2"]
# }

resource "aws_ssm_parameter" "project" {
  lifecycle {
    ignore_changes = [
      value,
    ]
  }

  name        = "${local.para_store_name}"
  description = "The redis connection for ${var.project_code}"
  type        = "SecureString"
  value       = jsonencode(
    {
      endpoint = aws_elasticache_serverless_cache.redis.endpoint
      reader_endpoint = aws_elasticache_serverless_cache.redis.reader_endpoint
    }
  )

  tags = merge(
    local.tags,
    {
      "Name" = "${local.para_store_name}notification" #because proj_desc is blank, thus there is already a -
    }
  )
}