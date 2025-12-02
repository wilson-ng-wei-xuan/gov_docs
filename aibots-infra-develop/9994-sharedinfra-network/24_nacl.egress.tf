module "nacl_rule_egress" {
################################################################################    
# we need to ALLOW 0.0.0.0/0 443 at the end instead of the typical DENY ALL.
# This is because we are using aws gateway endpoints for S3.
# This is a list of public IP to S3, managed by AWS.
################################################################################    

  source = "../modules/nacl_rule"

  deny_vpc_cidr = local.cidr_all # deny which cidr

  nacl_ids = local.nacl_egress

  nacl_rules = [
################################################################################
# outbound traffic
################################################################################
    # last rule is already 443
    # { # this allows 443 outbound
    #   action      = "allow"
    #   direction   = "outbound"
    #   from_port   = 443
    #   to_port     = 443
    #   cidr_block  = "0.0.0.0/0"
    # },
    { # this allows 587 outbound to aws ses smtp
      action      = "allow"
      direction   = "outbound"
      from_port   = 587
      to_port     = 587
      cidr_block  = "0.0.0.0/0"
    },

################################################################################    
# this is needed for ALB SSO, as the ALB will need to go out for OIDC.
################################################################################    
    {
      action      = "allow"
      direction   = "inbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_dmz[0]
    },
    {
      action      = "allow"
      direction   = "inbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_dmz[1]
    },

################################################################################
# app tier traffic
# note that routetable will route the traffic thru inspect NFW, transparent routing.
# by the network 101, the packet will show original SOURCE and DESTINATION
################################################################################
    { # allow app to go out
      action      = "allow"
      direction   = "inbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_app[0] # sharedsvc
    },
    { # allow app to go out
      action      = "allow"
      direction   = "inbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_app[1] # sharedsvc
    },
    { # allow app to go out
      action      = "allow"
      direction   = "inbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_app[2] # aibots
    },
    { # allow app to go out
      action      = "allow"
      direction   = "inbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_app[3] # aibots
    },

################################################################################    
# app tier STMP traffic
# the email-send api
################################################################################    
    {
      action      = "allow"
      direction   = "inbound"
      from_port   = 587
      to_port     = 587
      cidr_block  = local.subnet_app[0]
    },
    {
      action      = "allow"
      direction   = "inbound"
      from_port   = 587
      to_port     = 587
      cidr_block  = local.subnet_app[1]
    },

################################################################################    
# allow outbound direction to endpt
################################################################################    
    { # allow outbound direction to endpt
      action      = "allow"
      direction   = "outbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_endpt[0]
    },
    { # allow outbound direction to endpt
      action      = "allow"
      direction   = "outbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_endpt[1]
    },
  ]

  tags = local.tags # route does not have tags, but this is to align all codes.
}