module "nacl_rule_sharedsvc_db" {
################################################################################
# we need to ALLOW 0.0.0.0/0 443 at the end instead of the typical DENY ALL.
# This is because we are using aws gateway endpoints for S3.
# This is a list of public IP to S3, managed by AWS.
################################################################################

  source = "../modules/nacl_rule"

  deny_vpc_cidr = local.cidr_all # deny which cidr

  nacl_ids = local.nacl_sharedsvc_db

  nacl_rules = [
################################################################################
# allow inbound from sharedsvc app
################################################################################
    # { # allow inbound from cicd
    #   action      = "allow"
    #   direction   = "inbound"
    #   from_port   = 27017
    #   to_port     = 27017
    #   cidr_block  = data.aws_subnet.management_ez["${local.subnet_prefix}-a-${terraform.workspace}ezcicd-management"].cidr_block
    # },
    # { # allow inbound from cicd
    #   action      = "allow"
    #   direction   = "inbound"
    #   from_port   = 27017
    #   to_port     = 27017
    #   cidr_block  = data.aws_subnet.management_ez["${local.subnet_prefix}-b-${terraform.workspace}ezcicd-management"].cidr_block
    # },
    { # allow inbound from test
      action      = "allow"
      direction   = "inbound"
      from_port   = 27017
      to_port     = 27017
      cidr_block  = data.aws_subnet.management_ez["${local.subnet_prefix}-a-${terraform.workspace}eztest-management"].cidr_block
    },
    { # allow inbound from test
      action      = "allow"
      direction   = "inbound"
      from_port   = 27017
      to_port     = 27017
      cidr_block  = data.aws_subnet.management_ez["${local.subnet_prefix}-b-${terraform.workspace}eztest-management"].cidr_block
    },
    { # allow inbound from app
      action      = "allow"
      direction   = "inbound"
      from_port   = 27017
      to_port     = 27017
      cidr_block  = data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-a-${terraform.workspace}ezapp-sharedsvc"].cidr_block
    },
    { # allow inbound from app
      action      = "allow"
      direction   = "inbound"
      from_port   = 27017
      to_port     = 27017
      cidr_block  = data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-b-${terraform.workspace}ezapp-sharedsvc"].cidr_block
    },
    { # allow both from db
      action      = "allow"
      direction   = "both"
      from_port   = 27017
      to_port     = 27017
      cidr_block  = data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-a-${terraform.workspace}ezdb-sharedsvc"].cidr_block
    },
    { # allow both from db
      action      = "allow"
      direction   = "both"
      from_port   = 27017
      to_port     = 27017
      cidr_block  = data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-b-${terraform.workspace}ezdb-sharedsvc"].cidr_block
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