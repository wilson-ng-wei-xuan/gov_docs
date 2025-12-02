data "aws_network_acls" "default" {
  for_each  = toset( data.aws_vpcs.all.ids )
  vpc_id    = each.key

  filter {
    name   = "default"
    values = [true]
  }
}

resource "aws_default_network_acl" "default" {
  lifecycle {
    ignore_changes = [tags]
  }

  for_each  = { for entry in data.aws_network_acls.default: "${entry.vpc_id}" => entry }

  default_network_acl_id    = each.value.ids[0]
}