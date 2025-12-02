resource "aws_lb_listener_rule" "lb_listener_rule" {
  # create listener rule without SSO
  listener_arn  = var.listener_arn
  priority      = var.cognito_user_pool_domain == null ? var.priority : var.priority+1

  tags = merge(
    { "Name" = "${local.alb_lsnr_rule_name}-${var.family}" },
    local.tags
  )

  action {
    target_group_arn = aws_lb_target_group.lb_target_group.arn
    type             = "forward"
  }
  condition {
    host_header {
      values = var.host_header
    }
  }
  condition {
    path_pattern {
      values = [
        "${var.path_pattern}",
        "${var.path_pattern}*",
      ]
    }
  }
}

resource "aws_lb_listener_rule" "lb_listener_rule_sso" {
  # create listener rule with SSO
  count         = var.cognito_user_pool_domain == null ? 0 : 1
  listener_arn  = var.listener_arn
  priority      = var.priority

  tags = merge(
    { "Name" = "${local.alb_lsnr_rule_name}-${var.family}" },
    local.tags
  )

  action {
    type = "authenticate-cognito"

    authenticate_cognito {
      user_pool_arn       = var.aws_cognito_user_pools.arns[0]
      user_pool_client_id = aws_cognito_user_pool_client.client[0].id
      user_pool_domain    = var.cognito_user_pool_domain
      session_timeout     = 28800
    }
  }
  condition {
    host_header {
      values = var.host_header
    }
  }
  condition {
    path_pattern {
      values = [
        "/sso",
      ]
    }
  }

  action {
    target_group_arn = aws_lb_target_group.lb_target_group.arn
    type             = "forward"
  }
}

resource "aws_lb_target_group" "lb_target_group" {
  name                          = "${local.alb_tg_name}-${var.family}"

  deregistration_delay          = 15
  load_balancing_algorithm_type = "round_robin"
  port                          = var.port
  protocol                      = var.protocol
  protocol_version              = "HTTP1"
  slow_start                    = 0
  target_type                   = "ip"
  vpc_id                        = var.vpc_id

  tags = merge(
    local.tags,
    {
      "Name" = "${local.alb_tg_name}-${var.family}",
    }
  )

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = var.health_check_interval
    matcher             = "200-399"
    path                = var.health_check_path
    port                = var.port
    protocol            = var.protocol
    timeout             = 5
    unhealthy_threshold = 2
  }

  stickiness {
    enabled         = try(var.stickiness[ "enabled" ], true)
    type            = try(var.stickiness[ "type" ], "lb_cookie")
    cookie_duration = try(var.stickiness[ "cookie_duration" ], 86400)
    cookie_name     = try(var.stickiness[ "enabled" ], false) == false ? null : try(var.stickiness[ "cookie_name" ], "AWSALB")
  }
}