module "project_pub" {
  count = var.pub.host != null ? 1 : 0

  source = "../modules/fargate"

  # ecs task related
  family = "${var.project_code}-${var.project_desc}-${var.pub.name}"
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
  secretsmanager_secret_arn = [ data.aws_secretsmanager_secret.aibots_main.arn ]
  # secretsmanager_secret_arn = []
  ecr_repository_arn = [ aws_ecr_repository.project_pub[0].arn ]
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
                "ssm:GetParameter",
                "s3:GetObject",
                "s3:PutObject",
              ],
              Resource = [
                # analytics
                "${data.aws_s3_bucket.analytics.arn}",
                "${data.aws_s3_bucket.analytics.arn}/*",
                # email
                data.aws_secretsmanager_secret.aibots-smtp-user-no-reply.arn,
                "${data.aws_s3_bucket.email.arn}",
                "${data.aws_s3_bucket.email.arn}/*",
                # project
                "${data.aws_s3_bucket.aibots.arn}",
                "${data.aws_s3_bucket.aibots.arn}/*",
                aws_secretsmanager_secret.project[0].arn,
                data.aws_secretsmanager_secret.aibots_main.arn,
                # cloudfront
                "${data.aws_s3_bucket.aibots_cloudfront.arn}",
                "${data.aws_s3_bucket.aibots_cloudfront.arn}/*",
                data.aws_secretsmanager_secret.aibots_cloudfront.arn,
                data.aws_ssm_parameter.aibots_cloudfront.arn,
                # redis
                data.aws_ssm_parameter.aibots_api-redis.arn,
                # external api
                data.aws_ssm_parameter.aibots-cloak.arn,
                data.aws_ssm_parameter.aibots-llmstack.arn,
              ]
              Effect = "Allow"
            },
          ]
        },
      )
    },
    {
      name = "S3DeletePermissions"
      policy = jsonencode(
        {
          Version = "2012-10-17",
          Statement = [
            {
              Action = [
                "s3:DeleteObject",
              ],
              Resource = [
                  "${data.aws_s3_bucket.aibots_cloudfront.arn}",
                  "${data.aws_s3_bucket.aibots_cloudfront.arn}/*",
              ]
              Effect = "Allow"
            },
          ]
        },
      )
    },
    {
      name = "InvokeLambda"
      policy = jsonencode(
        {
          Version = "2012-10-17",
          Statement = [
            {
              Action = [
                "lambda:InvokeFunction",
              ],
              Resource = [
                data.aws_lambda_function.aibots-rag-aio-zip.arn,
                data.aws_lambda_function.aibots-rag-aio-img.arn,
              ]
              Effect = "Allow"
            },
          ]
        },
      )
    },
  ]

  container_definitions    = [ {
    name  = "${local.ecs_task_name}-${var.pub.name}",
    image = "${aws_ecr_repository.project_pub[0].repository_url}:latest",
    essential = true
    portMappings = [
      {
        protocol      = "tcp"
        containerPort = var.port
        hostPort      = var.port
      }
    ]

    # secrets = [
    #   { name = "EXAMPLE",valueFrom = "${data.aws_secretsmanager_secret.this_project_pub.arn}:EXAMPLE::" },
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
      { name = "NOUS_API__PTE_URL",value = local.SHAREDSVC_NOUS_API__PTE_URL },
      # # ADD YOUR VARIABLES HERE: analytics
      { name = "ANALYTICS__BUCKET", value = local.SHAREDSVC_ANALYTICS__BUCKET },
      { name = "ANALYTICS__PATH", value = "${var.project_code}/" },
      # # ADD YOUR VARIABLES HERE: email
      { name = "EMAIL_SEND__PTE_URL", value = local.SHAREDSVC_EMAIL_SEND__PTE_URL },
      { name = "EMAIL_SEND__BUCKET", value = local.SHAREDSVC_EMAIL__BUCKET },
      { name = "EMAIL_SEND__SECRET", value = local.AIBOTS_EMAIL_SMTP__SECRET },
      { name = "EMAIL_SEND__PATH", value = "${var.project_code}/" },
      # # ADD YOUR VARIABLES HERE: project
      { name = "PROJECT__PUB_URL", value = "https://${local.PUB_URL}" },
      { name = "PROJECT_API__PTE_URL", value = "https://${var.pte.host}${local.PTE_URL}" },
      { name = "PROJECT_API__PUB_URL", value = "https://${var.pub.host}${local.PUB_URL}" },
      { name = "PROJECT__BUCKET", value = local.AIBOTS_PROJECT__BUCKET },
      { name = "PROJECT__SECRET",value = resource.aws_secretsmanager_secret.project[0].name },
      { name = "PROJECT_DB__SECRET",value = local.AIBOTS_DB__SECRET },
      # { name = "PROJECT_RAG_OPENSEARCH__NAME",value = local.AIBOTS_RAG_OPENSEARCH__NAME },
      # { name = "PROJECT_RAG_OPENSEARCH__URL",value = local.AIBOTS_RAG_OPENSEARCH__URL },
      # # ADD YOUR VARIABLES HERE: latios
      # { name = "${replace("LATIOS_API__PTE_URL", "-", "_")}", value = local.SHAREDSVC_LATIOS_API__PTE_URL},
      # { name = "LATIOS_API__JWT_SECRET", value = "this is a secret" },
      # # ADD YOUR VARIABLES HERE: cloudfront
      { name = "CLOUDFRONT__PUB_URL", value = local.AIBOTS_CLOUDFRONT__PUB_URL },
      { name = "CLOUDFRONT__BUCKET",value = local.AIBOTS_CLOUDFRONT__BUCKET },
      { name = "CLOUDFRONT__SECRET",value = local.AIBOTS_CLOUDFRONT__SECRET },
      { name = "CLOUDFRONT__PARAM",value = local.AIBOTS_CLOUDFRONT__PARAM },
      # # ADD YOUR VARIABLES HERE: redis
      { name = "PROJECT_REDIS__PARAM",value = local.AIBOTS_API_REDIS__PARAM },
      # # ADD YOUR VARIABLES HERE: external api
      { name = "CLOAK__PARAM",value = local.AIBOTS_CLOAK__PARAM },
      { name = "LLMSTACK__PARAM",value = local.AIBOTS_LLMSTACK__PARAM },
      { name = "AIO__ARN",value = data.aws_lambda_function.aibots-rag-aio-img.arn },
      # { name = "SUPERUSERS",value = jsonencode( [ "louisa_ong@tech.gov.sg",
      #                                             "david_tw_lee@tech.gov.sg",
      #                                             "Leon_lim@tech.gov.sg",
      #                                             "vincent_ng@tech.gov.sg",
      #                                             "Quoc_thang_kieu@tech.gov.sg",
      #                                             "wilson_ng@tech.gov.sg",
      #                                             "Glenn_goh@tech.gov.sg",
      #                                             "Joseph_tan@tech.gov.sg",
      #                                             "Alex_ng@tech.gov.sg",
      #                                             "chadin_anuwattanaporn@tech.gov.sg",
      #                                             "Yeo_yong_kiat@tech.gov.sg",
      #                                             "Steven_koh@tech.gov.sg" ] ) },
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
  host_header = [ "${var.pub.host}${local.PUB_URL}" ]
  path_pattern = var.path_pattern
  priority = var.pte.host == null ? local.priority : local.priority + 1
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

  # sso
  cognito_user_pool_domain = var.sso == true ? local.cognito_user_pool_domain_wog-aad : null # Comes from data.0002-sharedinfra-cognito.tf.
  aws_cognito_user_pools = var.sso == true ? data.aws_cognito_user_pools.wog-aad : null 

  # aws_ecs_service
  security_groups = [ data.aws_security_group.aibots_ez["${local.secgrp_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
                      data.aws_security_group.aibots_api-redis.id ]
  # subnets = [ data.aws_subnet.aibots_ez["${local.subnet_prefix}-${local.az_deployment}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]
  subnets = [ data.aws_subnet.aibots_ez["${local.subnet_prefix}-a-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
              data.aws_subnet.aibots_ez["${local.subnet_prefix}-b-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]

  # cloudwatch metric alarm
  # if you provide this, it will create a cloudwatch_metric_alarm that will trigger at CPUUtilization 60%
  # if you don't want the metric, you have to set it to null
  cw_alarm_sns_topic_arn = data.aws_sns_topic.notification.arn

  # cloudwatch logs subscriptionFilters
  filter_pattern = var.filter_pattern
  destination_arn = data.aws_lambda_function.notification.arn

  tags = local.tags
}