module "nacl_rule_cicd" {
################################################################################
# we need to ALLOW 0.0.0.0/0 443 at the end instead of the typical DENY ALL.
# This is because we are using aws gateway endpoints for S3.
# This is a list of public IP to S3, managed by AWS.
################################################################################

  source = "../modules/nacl_rule"

  allow_ssh_rdp = false
  # deny_vpc_cidr = local.cidr_all # deny which cidr

  nacl_ids = local.nacl_cicd

  nacl_rules = [
################################################################################    
# allow ssh from SEED
################################################################################    
    # {
    #   action      = "allow"
    #   direction   = "inbound"
    #   from_port   = 22
    #   to_port     = 22
    #   cidr_block  = "8.29.230.18/32"
    # },
    # {
    #   action      = "allow"
    #   direction   = "inbound"
    #   from_port   = 22
    #   to_port     = 22
    #   cidr_block  = "8.29.230.19/32"
    # },
################################################################################    
# allow ssh from AWS
# https://docs.aws.amazon.com/cloud9/latest/user-guide/ip-ranges.html
# https://ip-ranges.amazonaws.com/ip-ranges.json
################################################################################    
    # {
    #   action      = "allow"
    #   direction   = "inbound"
    #   from_port   = 22
    #   to_port     = 22
    #   cidr_block  = "13.250.186.128/27"
    # },
    # {
    #   action      = "allow"
    #   direction   = "inbound"
    #   from_port   = 22
    #   to_port     = 22
    #   cidr_block  = "13.250.186.160/27"
    # },
################################################################################    
# Outbound
################################################################################    
    # outbound 443 is allow by default to 0.0.0.0/0 so that the dev machine can install needed packages
    # outbound 80 is also needed
    {
      action      = "allow"
      direction   = "outbound"
      from_port   = 80
      to_port     = 80
      cidr_block  = "0.0.0.0/0"
    },
    # # outbound 27017 to workload range
    # {
    #   action      = "allow"
    #   direction   = "outbound"
    #   from_port   = 27017
    #   to_port     = 27017
    #   cidr_block  = "172.31.0.0/16" # PRD
    # },
    # {
    #   action      = "allow"
    #   direction   = "outbound"
    #   from_port   = 27017
    #   to_port     = 27017
    #   cidr_block  = "172.30.0.0/16" # UAT
    # },
    # {
    #   action      = "allow"
    #   direction   = "outbound"
    #   from_port   = 27017
    #   to_port     = 27017
    #   cidr_block  = "172.29.0.0/16" # SIT
    # },
  ]

  tags = local.tags # route does not have tags, but this is to align all codes.
}