output ecs_cluster {
  value = aws_ecs_cluster.ecs_cluster  
}

output ecs_cluster_capacity_providers {
  value = aws_ecs_cluster_capacity_providers.ecs_cluster_capacity_providers
}

output ecs_task_definition {
  value = aws_ecs_task_definition.ecs_task_definition
}

output ecs_service {
  value = aws_ecs_service.ecs_service
}

output task_role {
  value = aws_iam_role.task_role
}

output execution_role {
  value = aws_iam_role.execution_role
}

output cloudwatch_log_group {
  value = module.cloudwatch_log_group.cloudwatch_log_group
}

output lb_listener_rule {
  value = aws_lb_listener_rule.lb_listener_rule
}

output lb_target_group {
  value = aws_lb_target_group.lb_target_group
}

# output cloudwatch_metric_alarm_CPUUtilization {
#   value = aws_cloudwatch_metric_alarm.CPUUtilization
# }

# output cloudwatch_metric_alarm_MemoryUtilization {
#   value = aws_cloudwatch_metric_alarm.MemoryUtilization
# }
