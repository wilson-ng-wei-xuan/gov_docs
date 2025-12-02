resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat.id
  subnet_id     = data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-${local.az_deployment}-${terraform.workspace}ezegress-sharedinfra"].id

  tags = merge(
    local.tags,
    { "Name"         = "${local.nat_name}" }
  )
}

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = merge(
    local.tags,
    { "Name"         = "${local.nat_name}" }
  )
}
