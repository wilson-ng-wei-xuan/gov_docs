# only the first private host header will get to create with the route53 record
# because you need to match the host header to the r53_zone, too much programming.
resource "aws_route53_record" "project_pte" {
  count = var.pte.host != null ? 1 : 0

  zone_id = data.aws_route53_zone.aibots_gov_sg.id
  name    = "${var.pte.host == null ? "not_set" : var.pte.host}${local.PTE_URL}"
  type    = "A"

  alias {
    name                   = data.aws_lb.ezdmzalb_pte.dns_name
    zone_id                = data.aws_lb.ezdmzalb_pte.zone_id
    evaluate_target_health = true
  }
}
