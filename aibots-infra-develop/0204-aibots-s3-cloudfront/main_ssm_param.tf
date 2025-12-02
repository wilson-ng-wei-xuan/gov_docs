# data "aws_ssm_parameter" "whatever" {
#   name = aws_ssm_parameter.secret.name
# }
# # this is how you use it.
# resource "something" "name" {
#   "element_1" = jsondecode(data.aws_ssm_parameter.whatever.value)["key_1"]
#   "element_2" = jsondecode(data.aws_ssm_parameter.whatever.value)["key_2"]
# }

resource "aws_ssm_parameter" "publickey" {
  count = var.secret_rotation == false ? 0 : 1

  lifecycle {
    ignore_changes = [
      value,
    ]
  }

  name        = "${local.para_store_name}-publickey" #because proj_desc is blank, thus there is already a -
  description = "The is the cloudfront public key holder for ${var.project_code}"
  type        = "SecureString"
  value       = aws_cloudfront_public_key.project[count.index].id

  tags = merge(
    local.tags,
    {
      "Name" = "${local.para_store_name}-publickey" #because proj_desc is blank, thus there is already a -
    }
  )
}