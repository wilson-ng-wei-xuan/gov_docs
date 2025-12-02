data "aws_vpcs" "all" {
  tags = {
    Terraform = "true"
  }
}