resource "aws_eip" "public_nlb" {
  count = 2
  domain = "vpc"

  tags = merge(
    local.tags,
    # Cannot reference to the nlb name directly, circular referencing
    { "Name"  = "${local.nlb_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}-pub" }
  )
}