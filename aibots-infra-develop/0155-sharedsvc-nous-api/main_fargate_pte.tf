module "project_pte" {
  count = var.pte.host != null ? 1 : 0

  source = "../modules/fargate"

  # ecs task related
  family = "${var.project_code}-${var.project_desc}-${var.pte.name}"
  cpu = var.cpu
  memory = var.memory
  desired_count = var.desired_count # desired_count must be in the range of min_capacity and max_capacity
  min_capacity = var.min_capacity
  max_capacity = var.max_capacity

  # this is ADD capacity
  scale_out_threshold = var.scale_out_threshold # when the average CPU rise above this value
  scale_out_evaluation_periods = var.scale_out_evaluation_periods # for this number of minutes
  scale_out_workload_percent = var.scale_out_workload_percent # scale out by this percent of workload
  scale_out_cooldown = var.scale_out_cooldown # and wait before the next scaling can trigger.

  # this is REDUCE capacity
  scale_in_threshold = var.scale_in_threshold # when the average CPU fall below this value
  scale_in_evaluation_periods = var.scale_in_evaluation_periods # for this number of minutes
  scale_in_workload_percent = var.scale_in_workload_percent # scale in by this percent of workload
  scale_in_cooldown = var.scale_in_cooldown # and wait before the next scaling can trigger.

  task_role_managed_policy_arns = var.task_role_managed_policy_arns
  secretsmanager_secret_arn = [ data.aws_secretsmanager_secret.sharedsvc_main.arn ]
  # secretsmanager_secret_arn = []
  ecr_repository_arn = [ aws_ecr_repository.project_pte[0].arn ]
  ecs_stop_task = data.aws_lambda_function.ecs_stop_task

  # task_role_managed_policy_arns = var.task_role_managed_policy_arns
  task_role_inline_policy = [
    {
      name = "AllowPermissions"
      policy = jsonencode(
        {
          Version = "2012-10-17",
          Statement = [
            {
              Action = [
                "secretsmanager:GetSecretValue",
                "s3:GetObject",
                "s3:PutObject",
                "ssm:GetParameter"
              ],
              Resource = [
                  data.aws_secretsmanager_secret.sharedsvc_main.arn,
                  "${data.aws_s3_bucket.analytics.arn}",
                  "${data.aws_s3_bucket.analytics.arn}/*",
                  aws_ssm_parameter.aoai.arn
              ]
              Effect = "Allow"
            },
          ]
        }
      )
    },
  ]

  container_definitions    = [ {
    name  = "${local.ecs_task_name}-${var.pte.name}",
    image = "${aws_ecr_repository.project_pte[0].repository_url}:latest",
    essential = true
    portMappings = [
      {
        protocol      = "tcp"
        containerPort = var.port
        hostPort      = var.port
      }
    ]

    # secrets = [
    #   { name = "EXAMPLE",valueFrom = "${data.aws_secretsmanager_secret.this_project_pte.arn}:EXAMPLE::" },
    # ]

    environment = [
      { name = "AWS_ID", value = data.aws_caller_identity.current.account_id },
      { name = "AWS_REGION", value = data.aws_region.current.name },
      { name = "COMPONENT", value = "${var.project_code}-${var.project_desc}" },
      { name = "DEBUG", value = "0" },
      { name = "HOST", value = "0.0.0.0" },
      { name = "PORT", value = tostring( var.port ) },
      { name = "USE_SSL", value = "1" },
      # { name = "SSL_KEYFILE", value = "localhost-privkey.pem" },
      # { name = "SSL_CERTFILE", value = "localhost-cert.pem" },
      # # ADD YOUR VARIABLES HERE: nous
      # { name = "NOUS_API__PTE_URL",value = local.SHAREDSVC_NOUS_API__PTE_URL },
      # # ADD YOUR VARIABLES HERE: analytics
      { name = "ANALYTICS__BUCKET", value = local.SHAREDSVC_ANALYTICS__BUCKET },
      { name = "ANALYTICS__PATH", value = "${var.project_code}/" },
      # # ADD YOUR VARIABLES HERE: email
      # { name = "EMAIL_SEND__PTE_URL", value = local.SHAREDSVC_EMAIL_SEND__PTE_URL },
      # { name = "EMAIL_SEND__BUCKET", value = local.SHAREDSVC_EMAIL__BUCKET },
      # { name = "EMAIL_SEND__SECRET", value = local.SHAREDSVC_EMAIL_SMTP__SECRET },
      # { name = "EMAIL_SEND__PATH", value = "${var.project_code}/" },
      # # ADD YOUR VARIABLES HERE: project
      # { name = "PROJECT__PUB_URL", value = "https://${local.PUB_URL}" },
      # { name = "PROJECT_API__PTE_URL", value = "https://${var.pte.host}${local.PTE_URL}" },
      # { name = "PROJECT_API__PUB_URL", value = "https://${var.pte.host}${local.PUB_URL}" },
      # { name = "PROJECT__BUCKET", value = local.SHAREDSVC_PROJECT__BUCKET },
      # { name = "PROJECT__SECRET",value = resource.aws_secretsmanager_secret.project[0].name },
      { name = "PROJECT_DB__SECRET",value = local.SHAREDSVC_DB__SECRET },
      { name = "PROJECT_AOAI__PARAM",value = aws_ssm_parameter.aoai.name },
    ]

    healthCheck = {
      retries =  3
      # command = [ "CMD-SHELL", "curl -k -f http://localhost:${var.ecs_port}${var.lb_target_group_health_check_path} || exit 1" ]
      # you need to install curl in your container to run the above proper healthcheck.
      # -k for ignore SSL certs
      # -f for fail fast with no output on server errors
      command = [ "CMD-SHELL", "ls || exit 1" ]
      timeout =  5
      interval =  15
      startPeriod = null
    }
    # logConfiguration will be provided by the module as the cloudwatch logs is created in module.
  } ]

  # lb related
  vpc_id = data.aws_lb.ezdmzalb_pte.vpc_id
  port = var.port
  protocol = var.protocol
  listener_arn = data.aws_lb_listener.ezdmzalb_pte_443.arn
  host_header = [ "${var.pte.host}${local.PTE_URL}" ]
  path_pattern = var.path_pattern
  priority = local.priority
  health_check_interval = var.health_check_interval
  health_check_path = var.health_check_path
  stickiness = { enabled = false } # BE fargate will disable cookie
  # stickiness = {} # use LB generated cookie, with 1 day duration
  # # FE fargate will let module fargate default to the below by not sending stickiness
  # # stickiness = {
  # #   enabled         = true
  # #   type            = "app_cookie"
  # #   cookie_duration = 3600
  # #   cookie_name     = "application-cookie" # as discussed with thang, we will standardise to this cookie name
  # # }

  # sso # pte do no have SSO
  cognito_user_pool_domain = null # default null means no sso needed
  aws_cognito_user_pools = null # default null means no sso needed

  # aws_ecs_service
  security_groups = [ data.aws_security_group.sharedsvc_ez["${local.secgrp_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id ]
  # subnets = [ data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-${local.az_deployment}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]
  subnets = [ data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-a-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
              data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-b-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]

  # cloudwatch metric alarm
  # if you provide this, it will create a cloudwatch_metric_alarm that will trigger at CPUUtilization 60%
  # if you don't want the metric, you have to set it to null
  cw_alarm_sns_topic_arn = data.aws_sns_topic.notification.arn

  # cloudwatch logs subscriptionFilters
  filter_pattern = var.filter_pattern
  destination_arn = data.aws_lambda_function.notification.arn

  tags = local.tags
}