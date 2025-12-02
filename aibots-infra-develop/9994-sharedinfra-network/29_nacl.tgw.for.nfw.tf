module "nacl_rule_tgw" {
################################################################################
# we need to ALLOW 0.0.0.0/0 443 at the end instead of the typical DENY ALL.
# This is because we are using aws gateway endpoints for S3.
# This is a list of public IP to S3, managed by AWS.
################################################################################

  source = "../modules/nacl_rule"

  deny_vpc_cidr = local.cidr_all # deny which cidr

  nacl_ids = local.nacl_tgw

  nacl_rules = [
################################################################################
# https://docs.aws.amazon.com/vpc/latest/tgw/tgw-nacls.html
# Best Practices
# Use a separate subnet for each transit gateway VPC attachment. For each subnet, use a small CIDR, for example /28, so that you have more addresses for EC2 resources. When you use a separate subnet, you can configure the following:
# Keep the inbound and outbound NACL that is associated with the transit gateway subnets open.
# Depending on your traffic flow, you can apply NACLs to your workload subnets.
################################################################################
    {
      action      = "allow"
      direction   = "inbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = "0.0.0.0/0"
    },
    {
      action      = "allow"
      direction   = "outbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = "0.0.0.0/0"
    },
    {
      action      = "allow"
      direction   = "inbound"
      from_port   = 587
      to_port     = 587
      cidr_block  = "0.0.0.0/0"
    },
    {
      action      = "allow"
      direction   = "outbound"
      from_port   = 587
      to_port     = 587
      cidr_block  = "0.0.0.0/0"
    },
  ]

  tags = local.tags # route does not have tags, but this is to align all codes.
}