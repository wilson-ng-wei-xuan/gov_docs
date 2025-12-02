variable "name" {
  type        = string
  description = <<EOT
    (Required) The name of the resource, e.g. myapigw. This will be used in the name of the resources.
  EOT
}
##
## apigw specific variables
##
variable "apigw_allowed_vpce" {
  type        = list
  description = <<EOT
    (Required) Set of VPC Endpoint identifiers.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_rest_api#vpc_endpoint_ids
  EOT
}