resource "aws_lb_target_group" "lb_target_group" {
  # lifecycle {
  #   ignore_changes = [
  #     # Ignore changes to tags, e.g. because the lambda will add additional tags on create
  #     tags,
  #   ]
  # }

  name                          = "${local.target_grp_name}"

  deregistration_delay          = 15
  load_balancing_algorithm_type = "round_robin"
  port                          = var.ecs_port
  protocol                      = "HTTP"
  protocol_version              = "HTTP1"
  slow_start                    = 0
  target_type                   = "ip"
  vpc_id                        = data.aws_vpc.sharedinfra_ez.id

  tags = merge(
    local.context_tags,
    {
      "Name" = "${local.target_grp_name}",
    }
  )

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 15
    matcher             = "200-399"
    path                = var.lb_target_group_health_check_path
    port                = var.ecs_port
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  stickiness {
    cookie_duration = 86400
    enabled         = false
    type            = "lb_cookie"
  }
}