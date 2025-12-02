# data "aws_ssm_parameter" "whatever" {
#   name = aws_ssm_parameter.secret.name
# }
# # this is how you use it.
# resource "something" "name" {
#   "element_1" = jsondecode(data.aws_ssm_parameter.whatever.value)["key_1"]
#   "element_2" = jsondecode(data.aws_ssm_parameter.whatever.value)["key_2"]
# }

resource "aws_ssm_parameter" "notification" {
  lifecycle {
    ignore_changes = [
      value,
    ]
  }

  name        = "${local.para_store_name}notification" #because proj_desc is blank, thus there is already a -
  description = "The notification URL and channel for ${var.project_code}"
  type        = "SecureString"
  value       = jsonencode(
    {
      notification_url = "DEFAULT",
      notification_channel = "DEFAULT"
      notification_message = "PLACE HOLDER, TO BE SET BY APP"
    }
  )

  tags = merge(
    local.tags,
    {
      "Name" = "${local.para_store_name}notification" #because proj_desc is blank, thus there is already a -
    }
  )
}