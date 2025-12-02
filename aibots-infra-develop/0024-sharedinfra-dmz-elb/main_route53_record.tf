locals{
  records = [ "${local.PUB_URL}" ]
}
resource "aws_route53_record" "project" {
  for_each = toset( local.records )
  zone_id = data.aws_route53_zone.aibots_gov_sg.zone_id
  name    = "${each.value}"
  type    = "A"

  alias {
    name                   = module.private_alb.lb.dns_name
    zone_id                = module.private_alb.lb.zone_id
    evaluate_target_health = true
  }
}