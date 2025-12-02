data "aws_security_group" "launchpad_ez_app" {
  filter {
    name     = "tag:terraform"
    values = ["true"]
  }
  filter {
    name   = "tag:project-code"
    values = ["launchpad"]
  }
  filter {
    name   = "tag:zone"
    values = ["ez"]
  }
  filter {
    name   = "tag:tier"
    values = ["app"]
  }
}