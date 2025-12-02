output "aws_vpc_endpoints_list" {
  value       = aws_vpc_endpoint.interface_endpt
  description = <<-EOT
    The list of endpoints created.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint
  EOT
}

output "aws_route53_zones_list" {
  value       = aws_route53_zone.interface_endpt
  description = <<-EOT
    The list of route53_zones created.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_zone
  EOT
}

# get the string after the last dot as the key
output "aws_vpc_endpoint_map"{
  value = {
    for endpoint in aws_vpc_endpoint.interface_endpt:
      split(".", endpoint.service_name)[length(split(".", endpoint.service_name))-1] => endpoint
  }
  description = <<-EOT
    The map of endpoints created with the service identifier as the key.
    e.g 
    ```
    {
      "ec2messages" = {
        "id" = "vpce-0e1f2f3f4f5f6f7f8"
        "service_name" = "com.amazonaws.ap-southeast-1.ec2messages"
        "vpc_endpoint_type" = "Interface"
        "subnet_ids" = [
          "subnet-0e1f2f3f4f5f6f7f8",
          "subnet-0e1f2f3f4f5f6f7f9",
        ]
        "security_group_ids" = [
          "sg-0e1f2f3f4f5f6f7f8",
        ]
        "private_dns_enabled" = false
        "tags" = {
          "Name" = "vpce-ap-southeast-1-dev-ec2messages"
          "env" = "dev"
          "zone" = "ap-southeast-1"
        }
      }
    }
    ```
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint
  EOT
}