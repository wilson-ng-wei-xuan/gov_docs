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
  description = "The is current ${var.project_code} least used aoss."
  type        = "SecureString"
  value       = jsonencode(
    {
      Endpoint    = data.aws_opensearchserverless_collection.aibots_rag.collection_endpoint
      Collection  = data.aws_opensearchserverless_collection.aibots_rag.name
    }
  )

  tags = merge(
    local.tags,
    {
      "Name" = "${local.para_store_name}"
    }
  )
}