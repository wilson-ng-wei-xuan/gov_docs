resource "aws_lb_listener_rule" "lb_listener_rule" {
  lifecycle {
    ignore_changes = [
      # Ignore changes to priority
      priority,
    ]
  }

  listener_arn = data.aws_lb_listener.ezingressalb_listen_443.arn
  priority     = var.lb_listener_rule_priority
  tags = merge(
    { "Name" = "${local.listener_rule_name}" },
    local.context_tags
  )

  action {
    target_group_arn = aws_lb_target_group.lb_target_group.arn
    type             = "forward"
  }
  condition {
    host_header {
      values = var.lb_listener_rule_host_header
    }
  }
  condition {
    path_pattern {
      values = [
        "/${var.project_code}",
        "/${var.project_code}/*",
      ]
    }
  }
# condition {
#     source_ip {
#       values = var.whitelist_ip
#     }
#   }
}