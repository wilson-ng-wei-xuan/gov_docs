# update your project specific environmental 

secret_rotation_schedule_expression = "cron( 0 20 * * ? * )" # everyday at 4am

retention_in_days = 365

deploy_igw = true

# environments are seperated at /16, i.e.:
# 172.31.0.0/16 << Prod
# 172.30.0.0/16 << UAT
# 172.29.0.0/16 << SIT
# 172.28.0.0/16
# We will skip the first 2 /24 in case we need to deploy something standard
vpc_cidr_block = null

subnets = [
  {
    name               = "ingress" # identifying short name, the rest of the name will be appended
    tier               = "ingress" # use as is in the tagging
    cidr_blocks        = ["100.127.130.0/28", "100.127.130.16/28"]
    share_route_table  = true
    assign_public_ipv4 = false
  },
  {
    name               = "dmz" # identifying short name, the rest of the name will be appended
    tier               = "dmz" # use as is in the tagging
    cidr_blocks        = ["100.127.130.32/28", "100.127.130.48/28"]
    share_route_table  = true
    assign_public_ipv4 = false
  },
  {
    name               = "egress" # identifying short name, the rest of the name will be appended
    tier               = "egress" # use as is in the tagging
    cidr_blocks        = ["100.127.130.64/28", "100.127.130.80/28"]
    share_route_table  = true
    assign_public_ipv4 = false
  },
  {
    name               = "inspect" # identifying short name, the rest of the name will be appended
    tier               = "inspect" # use as is in the tagging
    cidr_blocks        = ["100.127.130.96/28", "100.127.130.112/28"]
    share_route_table  = true
    assign_public_ipv4 = false
  },
  {
    name               = "tgw" # identifying short name, the rest of the name will be appended
    tier               = "tgw" # use as is in the tagging
    cidr_blocks        = ["100.127.130.128/28", "100.127.130.144/28"]
    share_route_table  = true
    assign_public_ipv4 = false
  },

  {
    name               = "endpt" # identifying short name, the rest of the name will be appended
    tier               = "endpt" # use as is in the tagging
    cidr_blocks        = ["100.127.130.192/27", "100.127.130.224/27"]
    share_route_table  = true
    assign_public_ipv4 = false
  },
]