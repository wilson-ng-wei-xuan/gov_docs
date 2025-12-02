resource "aws_shield_protection" "public_nlb" {
  count = 2

  name         = aws_eip.public_nlb[count.index].tags.Name
  resource_arn = "arn:aws:ec2:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:eip-allocation/${aws_eip.public_nlb[count.index].id}"

  tags = merge(
    local.tags,
    { "Name"  = module.public_nlb.lb.name }
  )
}
