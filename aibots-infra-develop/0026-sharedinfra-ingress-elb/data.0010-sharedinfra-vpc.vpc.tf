data "aws_vpc" "sharedinfra_ez" {
  filter {
    name   = "tag:request_uuid"
    values = ["1717143992286218365","1717143957961173913","1717143938954882050"]
  }
  filter {
    name   = "tag:cmp_compartment_type"
    values = ["Internet"]
  }
  filter {
    name   = "tag:gcc:team"
    values = ["gcci"]
  }
  filter {
    name   = "tag:type"
    values = ["Internet"]
  }
}