module "nacl_rule_dmz" {
################################################################################    
# we need to ALLOW 0.0.0.0/0 443 at the end instead of the typical DENY ALL.
# This is because we are using aws gateway endpoints for S3.
# This is a list of public IP to S3, managed by AWS.
################################################################################    

  source = "../modules/nacl_rule"

  deny_vpc_cidr = local.cidr_all # deny which cidr

  nacl_ids = local.nacl_dmz

  nacl_rules = [
################################################################################    
# Allow inbound for NLB to ALB forwarding.
# while on paper, it seems we only need to allow the ingress IP, but:
# # NLB targetting ALB, will turn on Preserve Client IP,
# # AWS magic will still return the traffic back to the NLB as "real" source
# # this will prevent the asyn routing
################################################################################    
    { # Allow inbound tcp 80 for NLB to ALB forwarding.
      action      = "allow"
      direction   = "inbound"
      from_port   = 80
      to_port     = 80
      cidr_block  = "0.0.0.0/0"
    },
    { # Allow inbound tcp 443 for NLB to ALB forwarding.
      action      = "allow"
      direction   = "inbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = "0.0.0.0/0"
    },

################################################################################    
# this is needed for ALB SSO, as the ALB will need to go out for OIDC.
# But we remark this away because NACL module has this rule as the last rule.
# Putting it here will over write the order.
################################################################################    
    # {
    #   action      = "allow"
    #   direction   = "outbound"
    #   from_port   = 443
    #   to_port     = 443
    #   cidr_block  = "0.0.0.0/0"
    # },

################################################################################    
# we allow "both" because:
# # allow outbound to app
# # allow inbound from app for communications to sharedsvc via the ALB in ingress
# do note that direction="both" means TCP ALL, the 443 in this case has not effect.
# it is just here for record purpose in case you need to do outbound and inbound seperately
################################################################################    
    {
      action      = "allow"
      direction   = "both"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_app[0] # sharedsvc
    },
    {
      action      = "allow"
      direction   = "both"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_app[1] # sharedsvc
    },
    {
      action      = "allow"
      direction   = "both"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_app[2] # aibots
    },
    {
      action      = "allow"
      direction   = "both"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_app[3] # aibots
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