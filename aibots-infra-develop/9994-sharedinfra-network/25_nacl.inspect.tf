module "nacl_rule_inspect" {
################################################################################
# we need to ALLOW 0.0.0.0/0 443 at the end instead of the typical DENY ALL.
# This is because we are using aws gateway endpoints for S3.
# This is a list of public IP to S3, managed by AWS.
################################################################################

  source = "../modules/nacl_rule"

  deny_vpc_cidr = local.cidr_all # deny which cidr

  nacl_ids = local.nacl_inspect

  nacl_rules = [
################################################################################
# inspect tier traffic
# note that routetable will route the traffic thru inspect NFW, transparent routing.
# by the network 101, the packet will show original SOURCE and DESTINATION
################################################################################
    { # allow inbound for 443
      action      = "allow"
      direction   = "inbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = "0.0.0.0/0"
    },
    { # allow outbound for 443
      action      = "allow"
      direction   = "outbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = "0.0.0.0/0"
    },

    { # allow inbound for SMTP
      action      = "allow"
      direction   = "inbound"
      from_port   = 587
      to_port     = 587
      cidr_block  = "0.0.0.0/0"
    },
    { # allow outbound for SMTP
      action      = "allow"
      direction   = "outbound"
      from_port   = 587
      to_port     = 587
      cidr_block  = "0.0.0.0/0"
    },

# ################################################################################
# # inbound traffic
# ################################################################################
#     { # allow inbound from app
#       action      = "allow"
#       direction   = "inbound"
#       from_port   = 443
#       to_port     = 443
#       cidr_block  = local.subnet_app[0] # sharedsvc
#     },
#     { # allow inbound from app
#       action      = "allow"
#       direction   = "inbound"
#       from_port   = 443
#       to_port     = 443
#       cidr_block  = local.subnet_app[1] # sharedsvc
#     },
#     { # allow inbound from app
#       action      = "allow"
#       direction   = "inbound"
#       from_port   = 443
#       to_port     = 443
#       cidr_block  = local.subnet_app[2] # aibots
#     },
#     { # allow inbound from app
#       action      = "allow"
#       direction   = "inbound"
#       from_port   = 443
#       to_port     = 443
#       cidr_block  = local.subnet_app[3] # aibots
#     },

# ################################################################################
# # inbound SMTP traffic from sharedsvc
# ################################################################################
#     { # allow inbound from app
#       action      = "allow"
#       direction   = "inbound"
#       from_port   = 587
#       to_port     = 587
#       cidr_block  = local.subnet_app[0]
#     },
#     { # allow inbound from app
#       action      = "allow"
#       direction   = "inbound"
#       from_port   = 587
#       to_port     = 587
#       cidr_block  = local.subnet_app[1]
#     },

# ################################################################################
# # outbound traffic
# ################################################################################
#     { # allow outbound to egress
#       action      = "allow"
#       direction   = "outbound"
#       from_port   = 443
#       to_port     = 443
#       cidr_block  = local.subnet_egress[0]
#     },
#     { # allow outbound to egress
#       action      = "allow"
#       direction   = "outbound"
#       from_port   = 443
#       to_port     = 443
#       cidr_block  = local.subnet_egress[1]
#     },
#     { # allow outbound to egress
#       action      = "allow"
#       direction   = "outbound"
#       from_port   = 587
#       to_port     = 587
#       cidr_block  = local.subnet_egress[0]
#     },
#     { # allow outbound to egress
#       action      = "allow"
#       direction   = "outbound"
#       from_port   = 587
#       to_port     = 587
#       cidr_block  = local.subnet_egress[1]
#     },

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