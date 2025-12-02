resource "aws_default_security_group" "default" {
  lifecycle {
    ignore_changes = [tags]
  }

  for_each  = toset( data.aws_vpcs.all.ids )
  vpc_id    = each.key
  
  ingress   = []
  egress    = []
}