resource "aws_route53_zone" "project" {
  name = "${local.route53_zone_prefix}${var.hosted_zone_name}"

  vpc {
    vpc_id =   data.aws_vpc.sharedinfra_ez.id
  }

  lifecycle {
    ignore_changes = [ vpc ]
  }

  tags = local.tags
}