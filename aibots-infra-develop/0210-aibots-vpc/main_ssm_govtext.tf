# data "aws_ssm_parameter" "whatever" {
#   name = aws_ssm_parameter.secret.name
# }
# # this is how you use it.
# resource "something" "name" {
#   "element_1" = jsondecode(data.aws_ssm_parameter.whatever.value)["key_1"]
#   "element_2" = jsondecode(data.aws_ssm_parameter.whatever.value)["key_2"]
# }

resource "aws_ssm_parameter" "govtext" {
  lifecycle {
    ignore_changes = [
      value,
    ]
  }

  name        = "${local.para_store_name}govtext" #because proj_desc is blank, thus there is already a -
  description = "The govtext endpoint for ${var.project_code}"
  type        = "SecureString"
  value       = jsonencode(
    {
      endpoint = "change via console"
      key = "change via console"
      expiry = "change via console"
    }
  )
  overwrite   = true

  tags = merge(
    local.tags,
    {
      "Name" = "${local.para_store_name}govtext" #because proj_desc is blank, thus there is already a -
    }
  )
}