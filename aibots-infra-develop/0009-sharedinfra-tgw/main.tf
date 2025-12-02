resource "aws_ec2_transit_gateway" "tgw" {
  description = "${var.agency_code} ${var.dept} ${var.project_code} self managed TGW"

  auto_accept_shared_attachments = "disable"

  tags = merge(
    local.tags,
    { "Name" = "${local.tgw_name}" }
  )
}