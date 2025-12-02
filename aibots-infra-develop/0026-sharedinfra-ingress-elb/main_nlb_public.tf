module "public_nlb" {
  source = "../modules/lb"

  name   = "${var.project_code}-pub"
  internal      = false
  load_balancer_type = "network"

  vpc_id = data.aws_vpc.sharedinfra_ez.id
  subnet_ids = [
    data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-a-${terraform.workspace}ezingress-sharedinfra"].id,
    data.aws_subnet.sharedinfra_ez["${local.subnet_prefix}-b-${terraform.workspace}ezingress-sharedinfra"].id,
  ]
  security_group_ids = [
    data.aws_security_group.sharedinfra_ez["${local.secgrp_prefix}-${terraform.workspace}ezingress-sharedinfra"].id,
  ]
  subnet_mapping = aws_eip.public_nlb.*.id

  enable_deletion_protection = true
  force_destroy = true # this is a test environment, true for s3 easy destroy.
  ssl_policy    = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn = var.certificate_arn

  aws_s3_bucket_logging = data.aws_s3_bucket.access-logs-s3.id

  access_logs = {
    bucket = data.aws_s3_bucket.access-logs-elb.id
    # prefix = "${var.project_code}-nlb-pub"
  }

  tags = local.tags
}

################################################################################
# aws_lb_target_group
################################################################################
resource "aws_lb_target_group" "tg_nlb_80" {
  name        = "${local.nlb_tg_name}-80"
  target_type = "alb"
  port        = 80
  protocol    = "TCP"
  vpc_id      = data.aws_vpc.sharedinfra_ez.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 5
    timeout             = 2
    unhealthy_threshold = 2
    matcher             = "200-399"
    path                = "/lb/heartbeat"
    port                = "traffic-port"
    protocol            = "HTTP"
  }

  # tags = merge(
  #   {
  #     "Name"    = local.nlb_tg_name,
  #     "type"    = module.public_nlb.lb.load_balancer_type == "application" ?  local.alb_prefix: local.nlb_prefix
  #     "scheme"  = module.public_nlb.lb.internal ? "private" : "public"
  #   },
  #   local.tags
  # )
  tags = local.tags
}

resource "aws_lb_target_group" "tg_nlb_443" {
  name        = "${local.nlb_tg_name}-443"
  target_type = "alb"
  port        = 443
  protocol    = "TCP"
  vpc_id      = data.aws_vpc.sharedinfra_ez.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 5
    timeout             = 2
    unhealthy_threshold = 2
    matcher             = "200-399"
    path                = "/lb/heartbeat"
    port                = "traffic-port"
    protocol            = "HTTPS"
  }

  tags = merge(
    {
      "Name"    = local.nlb_tg_name,
      "type"    = module.public_nlb.lb.load_balancer_type == "application" ?  local.alb_prefix: local.nlb_prefix
      "scheme"  = module.public_nlb.lb.internal ? "private" : "public"
    },
    local.tags
  )
}

################################################################################
# aws_lb_target_group_attachment
################################################################################
resource "aws_lb_target_group_attachment" "tg_attachment_80" {
  target_group_arn = aws_lb_target_group.tg_nlb_80.arn
  # attach the ALB to this target group
  target_id        = data.aws_lb.ezdmzalb_pte.arn
  #  If the target type is alb, the targeted Application Load Balancer must have at least one listener whose port matches the target group port.
  port             = 80
}

resource "aws_lb_target_group_attachment" "tg_attachment_443" {
  target_group_arn = aws_lb_target_group.tg_nlb_443.arn
  # attach the ALB to this target group
  target_id        = data.aws_lb.ezdmzalb_pte.arn
  #  If the target type is alb, the targeted Application Load Balancer must have at least one listener whose port matches the target group port.
  port             = 443
}

################################################################################
# aws_lb_listener
################################################################################
resource "aws_lb_listener" "nlb_80" {
  load_balancer_arn = module.public_nlb.lb.arn
  port              = "80"
  protocol          = "TCP"
  # certificate_arn   = "arn:aws:iam::187416307283:server-certificate/test_cert_rab3wuqwgja25ct3n4jdj2tzu4"
  # alpn_policy       = "HTTP2Preferred"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_nlb_80.arn
  }

  tags = merge(
    {
      "type" = module.public_nlb.lb.load_balancer_type == "application" ?  local.alb_prefix: local.nlb_prefix
      "scheme" = module.public_nlb.lb.internal ? "private" : "public"
    },
    local.tags
  )
}

resource "aws_lb_listener" "nlb_443" {
  load_balancer_arn = module.public_nlb.lb.arn
  port              = "443"
  protocol          = "TCP"
  # certificate_arn   = "arn:aws:iam::187416307283:server-certificate/test_cert_rab3wuqwgja25ct3n4jdj2tzu4"
  # alpn_policy       = "HTTP2Preferred"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_nlb_443.arn
  }

  tags = merge(
    {
      "type" = module.public_nlb.lb.load_balancer_type == "application" ?  local.alb_prefix: local.nlb_prefix
      "scheme" = module.public_nlb.lb.internal ? "private" : "public"
    },
    local.tags
  )
}