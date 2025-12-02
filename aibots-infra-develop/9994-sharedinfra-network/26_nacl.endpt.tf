module "nacl_rule_endpt" {
################################################################################
# we need to ALLOW 0.0.0.0/0 443 at the end instead of the typical DENY ALL.
# This is because we are using aws gateway endpoints for S3.
# This is a list of public IP to S3, managed by AWS.
################################################################################

  source = "../modules/nacl_rule"

  deny_vpc_cidr = local.cidr_all # deny which cidr

  nacl_ids = local.nacl_endpt

  nacl_rules = [
################################################################################
# This is the endpoint subnet, so allow all 443 inbound.
# The 443 outbound is already allowed as last rule.
################################################################################
    {
      action      = "allow"
      direction   = "inbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = "0.0.0.0/0"
    },
  ]

  tags = local.tags # route does not have tags, but this is to align all codes.
}