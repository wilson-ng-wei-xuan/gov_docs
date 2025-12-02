data "aws_subnets" "launchpad_ez" {
  filter {
    name     = "tag:terraform"
    values = ["true"]
  }
  filter {
    name     = "tag:project-code"
    values = ["launchpad"]
  }
  filter {
    name     = "tag:zone"
    values = ["ez"]
  }
}