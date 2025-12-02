module "nacl_rule_aibots_app" {
################################################################################
# we need to ALLOW 0.0.0.0/0 443 at the end instead of the typical DENY ALL.
# This is because we are using aws gateway endpoints for S3.
# This is a list of public IP to S3, managed by AWS.
################################################################################

  source = "../modules/nacl_rule"

  deny_vpc_cidr = local.cidr_all # deny which cidr

  nacl_ids = local.nacl_aibots_app

  nacl_rules = [
################################################################################    
# we allow "both" because:
# # allow inbound from DMZ ALB
# # allow outbound to DMZ ALB for communications to sharedsvc via the ALB in DMZ
# do note that direction="both" means TCP ALL, the 443 in this case has not effect.
# it is just here for record purpose in case you need to do outbound and inbound seperately
################################################################################    
    { # allow inbound from dmz
      action      = "allow"
      direction   = "both"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_dmz[0]
    },
    { # allow inbound from dmz
      action      = "allow"
      direction   = "both"
      from_port   = 443
      to_port     = 443
      cidr_block  = local.subnet_dmz[1]
    },

################################################################################
# allow outbound direction to database
################################################################################
    { # allow outbound to mongo db
      action      = "allow"
      direction   = "outbound"
      from_port   = 27017
      to_port     = 27017
      cidr_block  = data.aws_subnet.aibots_ez["${local.subnet_prefix}-a-${terraform.workspace}ezdb-aibots"].cidr_block
    },
    { # allow outbound to mongo db
      action      = "allow"
      direction   = "outbound"
      from_port   = 27017
      to_port     = 27017
      cidr_block  = data.aws_subnet.aibots_ez["${local.subnet_prefix}-b-${terraform.workspace}ezdb-aibots"].cidr_block
    },
    { # allow outbound to opensearh db
      action      = "allow"
      direction   = "outbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = data.aws_subnet.aibots_ez["${local.subnet_prefix}-a-${terraform.workspace}ezdb-aibots"].cidr_block
    },
    { # allow outbound to opensearh db
      action      = "allow"
      direction   = "outbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = data.aws_subnet.aibots_ez["${local.subnet_prefix}-b-${terraform.workspace}ezdb-aibots"].cidr_block
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