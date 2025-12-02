data "aws_lb" "ezingressalb" {
  tags = {
    "project-code" = "sharedinfra"
    "environment" = "dev"
    "terraform" = "true"
    "tier" = "ingress"
    "zone" = "ez"
    "type" = "alb"
  }
}

data "aws_lb_listener" "ezingressalb_listen_443" {
  load_balancer_arn = data.aws_lb.ezingressalb.arn
  port              = 443
}
