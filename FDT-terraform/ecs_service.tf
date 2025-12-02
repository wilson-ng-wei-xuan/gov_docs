resource "aws_ecs_service" "ecs_service" {
  # lifecycle {
  #   ignore_changes = [
  #     # Ignore changes to tags, e.g. because the lambda will add additional tags on create
  #     tags,
  #   ]
  # }

  name                               = local.ecs_service_name
  cluster                            = aws_ecs_cluster.ecs_cluster.id
  # task_definition                    = "${aws_ecs_task_definition.ecs_task_definition.id}:${aws_ecs_task_definition.ecs_task_definition.revision}"
  task_definition                    = aws_ecs_task_definition.ecs_task_definition.arn
  desired_count                      = 1

  capacity_provider_strategy {
    base              = 0
    capacity_provider = var.capacity_provider
    weight            = 1
  }

  enable_ecs_managed_tags            = true
#  enable_execute_command             = false
  health_check_grace_period_seconds  = 60
#  launch_type                        = "FARGATE"
  platform_version                   = "1.4.0"
  propagate_tags                     = "SERVICE"
  scheduling_strategy                = "REPLICA"

  tags = merge(
    local.context_tags,
    {
      "Name" = local.ecs_service_name,
    }
  )

  deployment_circuit_breaker {
    enable   = false
    rollback = false
  }

  deployment_controller {
    type = "ECS"
  }

  load_balancer {
    container_name   = aws_ecs_task_definition.ecs_task_definition.id
    container_port   = var.ecs_port
    target_group_arn = aws_lb_target_group.lb_target_group.arn
  }

  network_configuration {
    # assign_public_ip = false # LEON
    assign_public_ip = true
    security_groups  = [ data.aws_security_group.launchpad_ez_app.id ]
    subnets          = data.aws_subnets.launchpad_ez.ids
  }

  timeouts {}
}