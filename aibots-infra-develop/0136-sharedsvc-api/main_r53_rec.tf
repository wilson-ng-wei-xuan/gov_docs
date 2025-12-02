resource "aws_route53_record" "project" {
  for_each  = { for entry in var.pte_api: "${entry.host}${local.PTE_URL}" => entry }

  zone_id = data.aws_route53_zone.aibots_gov_sg.id
  name    = "${each.value.host}${local.PTE_URL}"
  type    = "A"

  alias {
    name                   = data.aws_lb.ezdmzalb_pte.dns_name
    zone_id                = data.aws_lb.ezdmzalb_pte.zone_id
    evaluate_target_health = true
  }
}
