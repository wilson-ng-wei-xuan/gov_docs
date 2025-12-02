# update your project specific environmental 

secret_rotation_schedule_expression = "cron( 0 /4 * * ? * )" # every 4 hourly

retention_in_days = 365

deploy_igw = true

# environments are seperated at /16, i.e.:
# 172.31.0.0/16 << Prod
# 172.30.0.0/16 << UAT
# 172.29.0.0/16 << SIT
# 172.28.0.0/16
# We will skip the first 2 /24 in case we need to deploy something standard
vpc_cidr_block = "172.29.254.0/24"

subnets = [
  {
    name               = "cicd" # identifying short name, the rest of the name will be appended
    tier               = "cicd" # use as is in the tagging
    cidr_blocks        = ["172.29.254.0/27", "172.29.254.32/27"]
    share_route_table  = true
    assign_public_ipv4 = false
  },
  {
    name               = "test" # identifying short name, the rest of the name will be appended
    tier               = "test" # use as is in the tagging
    cidr_blocks        = ["172.29.254.64/27", "172.29.254.96/27"]
    share_route_table  = true
    assign_public_ipv4 = false
  },
  {
    name               = "tgw" # identifying short name, the rest of the name will be appended
    tier               = "tgw" # use as is in the tagging
    cidr_blocks        = ["172.29.254.224/28", "172.29.254.240/28"]
    share_route_table  = true
    assign_public_ipv4 = false
  }
]