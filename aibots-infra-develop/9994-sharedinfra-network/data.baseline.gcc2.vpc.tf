data "aws_ec2_transit_gateway" "gen" {
  filter {
    name   = "options.amazon-side-asn"
    values = ["65513"]
  }
}

data "aws_ec2_transit_gateway" "common_svc" {
  filter {
    name   = "options.amazon-side-asn"
    values = ["65514"]
  }
}

# data "aws_internet_gateway" "default" {
#   filter {
#     name   = "attachment.vpc-id"
#     values = [data.aws_vpc.sharedinfra_ez.id]
#   }
# }
