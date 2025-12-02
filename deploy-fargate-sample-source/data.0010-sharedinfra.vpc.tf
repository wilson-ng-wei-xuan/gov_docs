data "aws_vpc" "sharedinfra_ez" {
  filter {
    name     = "tag:Name"
    values = ["cmt-11980006"]
  }
}

	