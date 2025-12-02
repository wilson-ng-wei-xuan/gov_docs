locals{
  priority = split("-", local.path)[0]
  # host_header = var.pub.host != null ? [ "${var.pub.host}${data.aws_route53_zone.aibots_gov_sg.name}" ] : [ "${var.pte.host}${data.aws_route53_zone.aibots_gov_sg.name}" ]
}

resource "aws_lb_listener_certificate" "project" {
  count = length( var.certificate_arn )

  listener_arn    = data.aws_lb_listener.ezdmzalb_pte_443.arn
  certificate_arn = var.certificate_arn[count.index]
}
