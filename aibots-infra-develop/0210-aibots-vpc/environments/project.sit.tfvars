# update your project specific environmental 

retention_in_days = 365

deploy_igw = false

# environments are seperated at /16, i.e.:
# 172.31.0.0/16 << Prod
# 172.30.0.0/16 << UAT
# 172.29.0.0/16 << SIT
# 172.28.0.0/16
# We will skip the first 2 /24 in case we need to deploy something standard
vpc_cidr_block = "172.29.250.0/24"

subnets = [
  {
    name = "app" # identifying short name, the rest of the name will be appended
    tier = "app" # use as is in the tagging
    cidr_blocks = ["172.29.250.0/26", "172.29.250.64/26"]
    share_route_table = true
    assign_public_ipv4 = false
  },
  {
    name = "tgw" # identifying short name, the rest of the name will be appended
    tier = "tgw" # use as is in the tagging
    cidr_blocks = ["172.29.250.128/28","172.29.250.144/28"]
    share_route_table = true
    assign_public_ipv4 = false
  },
  {
    name = "db" # identifying short name, the rest of the name will be appended
    tier = "db" # use as is in the tagging
    cidr_blocks = ["172.29.250.224/28", "172.29.250.240/28"]
    share_route_table = true
    assign_public_ipv4 = false
  }
]