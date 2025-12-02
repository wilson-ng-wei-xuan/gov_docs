module "nacl_rule_ingress" {
################################################################################    
# we need to ALLOW 0.0.0.0/0 443 at the end instead of the typical DENY ALL.
# This is because we are using aws gateway endpoints for S3.
# This is a list of public IP to S3, managed by AWS.
################################################################################    

  source = "../modules/nacl_rule"

  deny_vpc_cidr = local.cidr_all # deny which cidr

  nacl_ids = local.nacl_ingress

  nacl_rules = [
################################################################################    
# allow inbound from internet
################################################################################    
    {
      action      = "allow"
      direction   = "inbound"
      from_port   = 80
      to_port     = 80
      cidr_block  = "0.0.0.0/0"
    },
    { # this will also allow app tier to call the internal ALB
      action      = "allow"
      direction   = "inbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = "0.0.0.0/0"
    },

################################################################################    
# Allow outbound for NLB to ALB forwarding.
################################################################################    
    { # Allow outbound tcp 80 for NLB to ALB forwarding.
      action      = "allow"
      direction   = "outbound"
      from_port   = 80
      to_port     = 80
      cidr_block  = local.subnet_dmz[0]
    },
    { # Allow outbound tcp 80 for NLB to ALB forwarding.
      action      = "allow"
      direction   = "outbound"
      from_port   = 80
      to_port     = 80
      cidr_block  = local.subnet_dmz[1]
    },
    { # Allow outbound tcp 443 for NLB to ALB forwarding.
      action      = "allow"
      direction   = "outbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_dmz[0]
    },
    { # Allow outbound tcp 443 for NLB to ALB forwarding.
      action      = "allow"
      direction   = "outbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_dmz[1]
    },

# ################################################################################    
# # allow outbound direction to endpt
# ################################################################################    
#     { # allow outbound direction to endpt
#       action      = "allow"
#       direction   = "outbound"
#       from_port   = 443
#       to_port     = 443
#       cidr_block  = local.subnet_endpt[0]
#     },
#     { # allow outbound direction to endpt
#       action      = "allow"
#       direction   = "outbound"
#       from_port   = 443
#       to_port     = 443
#       cidr_block  = local.subnet_endpt[1]
#     },
  ]

  tags = local.tags # route does not have tags, but this is to align all codes.
}