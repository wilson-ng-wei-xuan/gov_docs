# data "aws_ssm_parameter" "whatever" {
#   name = aws_ssm_parameter.secret.name
# }
# # this is how you use it.
# resource "something" "name" {
#   "element_1" = jsondecode(data.aws_ssm_parameter.whatever.value)["key_1"]
#   "element_2" = jsondecode(data.aws_ssm_parameter.whatever.value)["key_2"]
# }

resource "aws_ssm_parameter" "aoai" {
  lifecycle {
    ignore_changes = [
      value,
    ]
  }

  name        = "${local.para_store_name}-aoai"
  description = "The ${var.project_code} aoai connection"
  type        = "SecureString"
  value       = jsonencode(
    {
      API_KEY   = "UPDATE KEY IN CONSOLE"
      AZURE_URL = "https://update_this.azure-api.net"
    }
  )

  tags = merge(
    local.tags,
    {
      "Name" = "${local.para_store_name}-aoai"
    }
  )
}