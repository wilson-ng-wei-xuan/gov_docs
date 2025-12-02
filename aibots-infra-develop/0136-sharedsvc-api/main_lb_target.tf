######################################################################################
# ALB listener cert
######################################################################################
resource "aws_lb_listener_certificate" "lb_listener_cert" {
  # this is using for_each because it needs the additional != null condition which is not supported in count.
  # aws_lb_listener_certificate is standalone, not reference to in other resources
  for_each = { for entry in var.certificate_arn: entry.fqdn => entry if entry.arn != null }

  listener_arn    = data.aws_lb_listener.ezdmzalb_pte_443.arn
  certificate_arn = each.value.arn
}

######################################################################################
# ALB listener and Target Group
######################################################################################
resource "aws_lb_target_group" "lb_target_group" {
  for_each = { for entry in var.pte_api: "${entry.name}" => entry }

  name = "${local.alb_tg_name}-${each.value.name}"

  tags = merge(
    local.tags,
    {
      "Name" = "${local.alb_tg_name}-${each.value.name}",
    }
  )

  target_type = "lambda"
}

locals {
  priority = split("-", local.path)[0]
}

resource "aws_lb_listener_rule" "lb_listener_rule" {
  for_each = { for idx, entry in var.pte_api: "${entry.name}" => merge( entry, { myidx: idx } ) }
  # lifecycle {
  #   ignore_changes = [
  #     priority,
  #   ]
  # }
  
  listener_arn = data.aws_lb_listener.ezdmzalb_pte_443.arn
  priority   = var.lb_listener_rule_priority + local.priority + each.value.myidx

  tags = merge(
    local.tags,
    {
      "Name" = "${local.alb_lsnr_rule_name}-${each.value.name}",
    }
  )

  action {
    target_group_arn = aws_lb_target_group.lb_target_group[ each.value.name ].arn
    type             = "forward"
  }
  condition {
    host_header {
      values = ["${each.value.host}${local.PTE_URL}"]
    }
  }
  condition {
    path_pattern {
      values = each.value.path_pattern
    }
  }
}

######################################################################################
# give lambda the permission
######################################################################################
resource "aws_lambda_permission" "AllowExecutionFromlb" {
  for_each = { for entry in var.pte_api: "${entry.name}" => entry }

  statement_id  = "AllowExecutionFromlb"
  action        = "lambda:InvokeFunction"
  function_name = module.simple_lambda[ each.value.name ].lambda_function.arn
  principal     = "elasticloadbalancing.amazonaws.com"
  source_arn    = aws_lb_target_group.lb_target_group[ each.value.name ].arn
}

######################################################################################
# attach the lambda to the target group
######################################################################################
resource "aws_lb_target_group_attachment" "lb_target_group_attachment" {
  for_each = { for entry in var.pte_api: "${entry.name}" => entry }

  target_group_arn = aws_lb_target_group.lb_target_group[ each.value.name ].arn
  target_id    = module.simple_lambda[ each.value.name ].lambda_function.arn
  depends_on   = [aws_lambda_permission.AllowExecutionFromlb]
}