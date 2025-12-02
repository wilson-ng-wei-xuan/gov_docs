resource "aws_ecs_cluster" "ecs_cluster" {
  name = "${local.ecs_cluster_name}-${var.family}"

  setting {
    name  = "containerInsights"
    value = "enabled" # "${var.tags.Environment == "prd" ? "enabled" : "disabled" }"
  }

  tags = merge(
    local.tags,
    {
      "Name" = "${local.ecs_cluster_name}-${var.family}",
    }
  )
}

resource "aws_ecs_cluster_capacity_providers" "ecs_cluster_capacity_providers" {
  cluster_name = aws_ecs_cluster.ecs_cluster.name

  capacity_providers = [
    "FARGATE",
    "FARGATE_SPOT",
  ]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE_SPOT"
  }
}

# #This is to add logConfiguration to the definition
# # jsondecode << converts sting into json
# # merge to combine 2 json
# # jsonencode converts it back to strong
# # This is working
# locals {
#   container_definitions = merge(
#     var.container_definitions[0],
#     {
#       "logConfiguration" : {
#         "logDriver" : "awslogs"
#         "options" : {
#           "awslogs-group" : module.cloudwatch_log_group.cloudwatch_log_group.name
#           "awslogs-region" : data.aws_region.current.name
#           "awslogs-stream-prefix" : "ecs"
#         }
#       }
#     }
#   )
# }

locals {
  container_definitions = flatten(
    [for con_def in var.container_definitions :
      merge(
        con_def,
        {
          "logConfiguration" : {
            "logDriver" : "awslogs"
            "options" : {
              "awslogs-group" : module.cloudwatch_log_group.cloudwatch_log_group.name
              "awslogs-region" : data.aws_region.current.name
              "awslogs-stream-prefix" : "ecs"
            }
          }
        }
      )
    ]
  )
}

resource "aws_ecs_task_definition" "ecs_task_definition" {
  family                   = "${local.ecs_task_name}-${var.family}"
  # task role is permission for the application, e.g. read files in S3 bucket etc.
  task_role_arn            = aws_iam_role.task_role.arn
  # execution role is permission for the ECS agents, e.g. write to cloudwatch logs.
  execution_role_arn       = aws_iam_role.execution_role.arn
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  requires_compatibilities = ["FARGATE"]

  tags = merge(
    local.tags,
    {
      "Name" = "${local.ecs_task_name}-${var.family}",
    }
  )
  # # This is working
  # container_definitions = jsonencode( [ local.container_definitions ] )
  container_definitions = jsonencode( local.container_definitions )
}

resource "aws_ecs_service" "ecs_service" {
  name                               = "${local.ecs_service_name}-${var.family}"
  cluster                            = aws_ecs_cluster.ecs_cluster.id
  task_definition                    = aws_ecs_task_definition.ecs_task_definition.arn
  desired_count                      = var.desired_count == 0 ? var.min_capacity : var.desired_count

  capacity_provider_strategy {
    base              = 0
    capacity_provider = var.capacity_provider
    weight            = 1
  }

  enable_ecs_managed_tags            = true
#  enable_execute_command             = false
  health_check_grace_period_seconds  = var.health_check_grace_period_seconds
#  launch_type                        = "FARGATE"
  platform_version                   = "1.4.0"
  propagate_tags                     = "SERVICE"
  scheduling_strategy                = "REPLICA"

  tags = merge(
    local.tags,
    {
      "Name" = "${local.ecs_service_name}-${var.family}",
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
    container_port   = var.port
    target_group_arn = aws_lb_target_group.lb_target_group.arn
  }

  network_configuration {
    assign_public_ip = false
    security_groups  = var.security_groups
    subnets          = var.subnets
  }

  timeouts {}
}