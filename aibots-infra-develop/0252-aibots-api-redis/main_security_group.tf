################################################################################
# https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/elasticache-vpc-accessing.html#elasticache-vpc-accessing-same-vpc
resource "aws_security_group" "project" {
  name        = "${local.secgrp_name}"
  description = "${var.project_code}-${var.project_desc}"
  vpc_id      = data.aws_vpc.aibots_ez.id

  ingress {
    from_port = 6379 # default port
    to_port   = 6380 # reader port
    protocol  = "tcp"
    self      = true
  }

  egress {
    from_port = 6379 # default port
    to_port   = 6380 # reader port
    protocol  = "tcp"
    self      = true
  }

  tags = merge(
    local.tags,
    { "Name" = "${local.secgrp_name}" }
  )
}