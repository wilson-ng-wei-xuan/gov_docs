output "api_gateway_rest_api" {
  value       = aws_api_gateway_rest_api.apigw_rest_api
  description = <<-EOT
    The REST API Gateway.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_rest_api
  EOT
}

# output "api_gateway_request_validator" {
#   value       = aws_api_gateway_request_validator.apigw_request_validator
#   description = <<-EOT
#     The API Gateway Request Validator.
#     Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_request_validator
#   EOT
# }

output "api_gateway_rest_api_policy" {
  value       = aws_api_gateway_rest_api_policy.apigw_policy
  description = <<-EOT
    The API Gateway REST API Policy.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_rest_api_policy
  EOT
}
