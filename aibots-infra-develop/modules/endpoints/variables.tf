# variable "interface_endpt" {
#   type        = list(map(string))
#   description = <<EOT
#     (Required) The list of vpc interface endpoints to create.Provide the full service name 
#     e.g. ["com.amazonaws.ap-southeast-1.ec2messages","com.amazonaws.ap-southeast-1.monitoring","com.amazonaws.ap-southeast-1.ssm","com.amazonaws.ap-southeast-1.logs","com.amazonaws.ap-southeast-1.ssmmessages","com.amazonaws.ap-southeast-1.git-codecommit","com.amazonaws.ap-southeast-1.ec2","com.amazonaws.ap-southeast-1.sqs","com.amazonaws.ap-southeast-1.glue","com.amazonaws.ap-southeast-1.athena","com.amazonaws.ap-southeast-1.email-smtp"]
#     The interface endpoints are not limited to AWS services. You can create an interface endpoint to any service that supports AWS PrivateLink.
#     Refer to: https://docs.aws.amazon.com/vpc/latest/privatelink/aws-services-privatelink-support.html
#   EOT
# }

variable "interface_endpt" {
  type        = list(
    object(
      {
        service_name        = string
        name                = optional(string)
        restrict_oubound    = optional(bool, true)
        private_dns_enabled = optional(bool, false)
      }
    )
  )
  description = <<EOT
    (Required) The list of vpc interface endpoints to create.Provide the full service name 
    e.g. ["com.amazonaws.ap-southeast-1.ec2messages","com.amazonaws.ap-southeast-1.monitoring","com.amazonaws.ap-southeast-1.ssm","com.amazonaws.ap-southeast-1.logs","com.amazonaws.ap-southeast-1.ssmmessages","com.amazonaws.ap-southeast-1.git-codecommit","com.amazonaws.ap-southeast-1.ec2","com.amazonaws.ap-southeast-1.sqs","com.amazonaws.ap-southeast-1.glue","com.amazonaws.ap-southeast-1.athena","com.amazonaws.ap-southeast-1.email-smtp"]
    The interface endpoints are not limited to AWS services. You can create an interface endpoint to any service that supports AWS PrivateLink.
    Refer to: https://docs.aws.amazon.com/vpc/latest/privatelink/aws-services-privatelink-support.html
  EOT
}

variable "vpc_id" {
  type        = string
  description = <<EOT
    (Required) The VPC ID of the virtual private cloud in which the VPC interface endpoint will be created.
    https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint#vpc_id
  EOT
}

variable "subnet_ids" {
  type        = list(string)
  description = <<EOT
    (Required) A list of one or more subnets in which to create a network interface for the endpoint.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint#subnet_ids
  EOT
}

variable "security_group_ids" {
  type        = list(string)
  description = <<EOT
    (Required) A list of security groups IDs that are available to attach to your VPC interface endpoint.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint#security_group_ids
  EOT
}

# variable "private_dns_enabled" {
#   type        = bool
#   description = <<EOT
#     (Optional) Whether or not to associate a private hosted zone with the specified VPC.
#     Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint#private_dns_enabled
#   EOT
#   default     = false
# }
