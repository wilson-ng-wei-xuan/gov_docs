resource "aws_ecs_task_definition" "ecs_task_definition" {
  family                   = local.ecs_task_name
  # task role is permission for the application, e.g. read files in S3 bucket etc.
  task_role_arn            = aws_iam_role.task_role.arn ### LEON: this was hard coded in the container
  # execution role is permission for the ECS agents, e.g. write to cloudwatch logs.
  execution_role_arn       = aws_iam_role.execution_role.arn
  network_mode             = "awsvpc"
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  requires_compatibilities = ["FARGATE"]

  tags = merge(
    local.context_tags,
    {
      "Name" = local.ecs_task_name,
    }
  )

  container_definitions = jsonencode([
    {
      name          = local.ecs_task_name
      # image         = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.name}.amazonaws.com/${var.ecr_repo}:${var.image_tag}"
      image         = "${aws_ecr_repository.ecr_repository.repository_url}:${var.image_tag}"
      # cpu           = 0,
      # memory        = 1024,
      essential     = true
      portMappings  = [
        {
          protocol      = "tcp"
          containerPort = var.ecs_port
          hostPort      = var.ecs_port
        }
      ]

      essential = true,

      secrets = []

      environment: [
        { name = "HOST", value = "0.0.0.0" },
        { name = "PORT", value = "80" },
        { name = "LOGGING_LEVEL", value = "10" }
      ],
      # LOGGING_LEVEL
      # 10 - debug
      # 20 - info
      # 30 - warning
      # 40 - error
      # 50 - critical
      
      healthCheck = {
        retries =  3
        # command = [ "CMD-SHELL", "curl -k -f http://localhost:${var.ecs_port}${var.lb_target_group_health_check_path} || exit 1" ]
        # -k for ignore SSL certs
        # -f for fail fast with no output on server errors
        command = [ "CMD-SHELL", "ls || exit 1" ]
        timeout =  5
        interval =  15
        startPeriod = null
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group = aws_cloudwatch_log_group.cloudwatch_log_group.name
          awslogs-region = data.aws_region.current.name
          awslogs-stream-prefix = "ecs"
        }
      }
    },
  ])
}