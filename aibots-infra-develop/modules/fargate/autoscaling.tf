resource "aws_appautoscaling_target" "ecs_target" {
  count              = var.min_capacity > 0 && var.max_capacity > var.min_capacity ? 1 : 0
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${aws_ecs_cluster.ecs_cluster.name}/${aws_ecs_service.ecs_service.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  tags = merge(
    local.tags,
    {
      "Name" = "${local.ecs_cluster_name}-${var.family}",
    }
  )
}

resource "aws_appautoscaling_policy" "scaleout" {
  count              = var.min_capacity > 0 && var.max_capacity > var.min_capacity ? 1 : 0
  name               = "scaleout"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.ecs_target[count.index].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target[count.index].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target[count.index].service_namespace

  step_scaling_policy_configuration {
    adjustment_type          = "PercentChangeInCapacity"
    cooldown                 = var.scale_out_cooldown == 0 ? 2*var.health_check_grace_period_seconds : var.scale_out_cooldown
    metric_aggregation_type  = "Average"
    min_adjustment_magnitude = 1

    step_adjustment {
      metric_interval_lower_bound = 0
      scaling_adjustment          = var.scale_out_workload_percent
    }
  }
}

resource "aws_appautoscaling_policy" "scalein" {
  count              = var.min_capacity > 0 && var.max_capacity > var.min_capacity ? 1 : 0
  name               = "scalein"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.ecs_target[count.index].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target[count.index].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target[count.index].service_namespace

  step_scaling_policy_configuration {
    adjustment_type          = "PercentChangeInCapacity"
    cooldown                 = var.scale_in_cooldown == 0 ? 2*var.health_check_grace_period_seconds : var.scale_out_cooldown
    metric_aggregation_type  = "Average"
    min_adjustment_magnitude = 1

    step_adjustment {
      metric_interval_upper_bound = 0
      scaling_adjustment          = var.scale_in_workload_percent
    }
  }
}
