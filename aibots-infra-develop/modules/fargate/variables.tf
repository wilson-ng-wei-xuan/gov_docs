##################################
# cloudwatch_log_group
##################################
variable "retention_in_days" {
  type        = number
  default     = 365
  description = <<EOT
    (Optional) Specifies the number of days you want to retain log events in the specified log group.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group
  EOT
}

variable "destination_arn" {
  type        = string
  default     = null
  description = <<EOT
    The ARN of the destination to deliver matching log events to. Kinesis stream or Lambda function ARN.
    If not provided, the subscription filter will not be created.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_subscription_filter
  EOT
}

variable "filter_pattern" {
  type        = string
  default     = "?\"[NOTIFY]\" ?\"[ERROR]\" ?\"[WARNING]\" ?\"[WARN]\" ?\"[CRITICAL]\" ?\"caught SIGTERM, shutting down\""
  description = <<EOT
    CloudWatch Logs filter pattern for subscribing to a filtered stream of log events.
    Since we are deploying lambda, we just default it to something that is more Lambda.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_subscription_filter#filter_pattern
  EOT
}

##################################
# aws_ecs_task_definition
##################################
variable "family"{
  type = string
  description = <<EOT
    (Required) A unique name for your task definition.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_task_definition
  EOT

}

variable "task_role_managed_policy_arns" {
  type = list
  default = []
  description = <<EOT
    (Required) This module will create the IAM role for the task.
    Task role is permission for the application, e.g. read files in S3 bucket, SQS, SNS etc.
    Add in the managed_policy_arns needed by your application.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role
  EOT
}

variable "task_role_inline_policy" {
  type        = list( any )
  default     = []
  description = <<EOT
    (Optional) Inline policy to attach to the ECS task IAM role.
    task_role_inline_policy = [
      {
        name = "policy_name"
        policy = jsonencode(
          {
            Version = "2012-10-17",
            Statement = [
              {
                Action = [
                  "logs:CreateLogStream",
                  "logs:PutLogEvents",
                ],
                Resource = [
                    "resource.arn",
                ]
                Effect = "Allow"
              },
              {
                Action = "ecr:GetAuthorizationToken",
                Resource = "*",
                Effect = "Allow"
              },
            ]
          }
        )
      },
      {
        name = "policy_name"
        policy = jsonencode(
          {
            Blah = "blah"
          }
        )
      }
    ]
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role
  EOT
}

variable "execution_role_managed_policy_arns" {
  type = list
  default = ["arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"]
  description = <<EOT
    (Required) This module will create the IAM execution role for the task.
    Execution role is permission for the ECS agents, e.g. write to cloudwatch logs, retrieve Secrets to deploy task etc.
    AmazonECSTaskExecutionRolePolicy will be added by default.
    Add in the managed_policy_arns needed by your application.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role
  EOT
}

variable "ecr_repository_arn" {
  type = list
  description = <<EOT
    (Required) The ecr repo of the image used to start a container.
    This is use in the iam role execution_role to allow container to pull from the specific repo, and not any other repo.
  EOT
}

variable "cpu" {
  type = number
  description = <<EOT
    (Required) Number of cpu units used by the task.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_task_definition
    Refer to: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html
  EOT
}

variable "memory" {
  type = number
  description = <<EOT
    (Required) Amount (in MiB) of memory used by the task.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_task_definition
    Refer to: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html
  EOT
}

variable "health_check_grace_period_seconds" {
  type = number
  default = 60
  description = <<EOT
    (Optional) Seconds to ignore failing load balancer health checks on newly instantiated tasks to prevent premature shutdown.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_service#health_check_grace_period_seconds
  EOT
}

variable "container_definitions" {
  type = list
  description = <<EOT
    (Required) This is the container_definitions. It can be simple or complex. So I will leave it to you to write it.
    There are samples provided, you should reference and copy when possible.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_task_definition
  EOT
}

variable "secretsmanager_secret_arn" {
  type = list
  default = null
  description = <<EOT
    (Optional) If your task requires secrets, iam role execution_role will allow the task to get the secret by the arn.
    You will need to create the secret yourself.
  EOT
}

variable "vpc_id" {
  type = string
  description = <<EOT
    Identifier of the VPC in which to create the target group.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group
  EOT
}

variable "port" {
  type = number
  description = <<EOT
    Port on which targets receive traffic, unless overridden when registering a specific target.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group
  EOT
}

variable "protocol" {
  type = string
  description = <<EOT
    Protocol to use for routing traffic to the targets.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group#protocol
  EOT
}

variable "path_pattern" {
  type = string
  default = "/"
  description = <<EOT
    Path patterns to match against the request URL.
    example, path_pattern = "abc/" It will be translated to [ "abc/", "abc/*"]
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener_rule#path_pattern
  EOT
}

variable "health_check_interval" {
  type = number
  default = 30
  description = <<EOT
    Approximate amount of time, in seconds, between health checks of an individual target.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group#interval
  EOT
}

variable "health_check_path" {
  type = string
  default = "/"
  description = <<EOT
    Destination for the health check request.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group#path
  EOT
}

variable "capacity_provider" {
  type = string
  default = "FARGATE_SPOT"
  description = <<EOT
    Short name of the capacity provider, choose either FARGATE_SPOT or FARGATE
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_cluster_capacity_providers
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_service
  EOT
}

variable "subnets" {
  type = list
  description = <<EOT
    Subnets associated with the task or service.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_service#network_configuration
  EOT
}

variable "security_groups" {
  type = list
  description = <<EOT
    Security groups associated with the task or service.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_service#network_configuration
  EOT
}

variable "priority" {
  type = number
  default = null
  description = <<EOT
    The priority for the rule between 1 and 50000. Leaving it unset will automatically set the rule with next available priority after currently existing highest rule.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener_rule#priority
  EOT
}

variable "listener_arn" {
  type = string
  description = <<EOT
    The ARN of the listener to which to attach the rule.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener_rule#listener_arn
  EOT
}

variable "cognito_user_pool_domain" {
  type = string
  default = null # default null means no sso needed.
  description = <<EOT
    Comes from data.0006-sharedinfra-cognito.tf.
    If sso is created, it will be pathed "/sso"
  EOT
}

variable "aws_cognito_user_pools" {
  type = any
  default = null # default null means no sso needed.
  description = <<EOT
    Comes from data.0002-sharedinfra-cognito.tf.
    Pass in the data.aws_cognito_user_pools.wog-aad
    If sso is created, it will be pathed "/sso"
  EOT
}

variable "host_header" {
  type = list
  description = <<EOT
    Contains a list of host header patterns to match.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener_rule#condition-blocks
  EOT
}

variable "cw_alarm_sns_topic_arn" {
  type = string
  description = <<EOT
    SNS topic arn to trigger when cloudwatch alarm status change for:
    alarm_actions, ok_actions, insufficient_data_actions
    Set to null to disable alarm.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener_rule#condition-blocks
  EOT
}

variable "ecs_stop_task"{
  type = any
  default = null
  description = <<EOT
    (Optional) A lambda name to stop the ECS task on Image Push event trigger.
    If this is not provided, the Image Push event rule will be skipped.
  EOT
}

variable "stickiness"{
  type = map
  default = {
    enabled         = true
    type            = "app_cookie"
    cookie_duration = 3600
    cookie_name     = "application-cookie" # as discussed with thang, we will standardise to this cookie name
  }
  description = <<EOT
    (Optional) The stickiness of the target group.
    https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group#stickiness
  EOT
}

variable "desired_count" {
  type = number
  default = 0
  description = <<EOT
    Number of instances of the task definition to place and keep running.
    Setting this to 0 will set the the value to min_capacity
    If you really do not want to run the instance, just set all 3 values to 0.
      desired_count
      min_capacity
      max_capacity
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_service#desired_count
  EOT
}

variable "min_capacity"{
  type = number
  default = 1
  description = <<EOT
    Min capacity of the scalable target.
    Set to 0 if you do not require auto scaling
    https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/appautoscaling_target#min_capacity
  EOT
}

variable "max_capacity"{
  type = number
  default = 2
  description = <<EOT
    Min capacity of the scalable target.
    Set to 0 if you do not require auto scaling
    https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/appautoscaling_target#max_capacity
  EOT
}

variable "scale_out_threshold"{
  type = number
  default = 60
  description = <<EOT
    Target value for the metric to trigger, e.g. Average CPUUtilization > 60%
    https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm#target_threshold
  EOT
}
variable "scale_out_evaluation_periods"{
  type = number
  default = 3
  description = <<EOT
    The number of periods over which data is compared to the specified threshold, 1 datapoint is 1 minutes.
    https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm#evaluation_periods
  EOT
}
variable "scale_out_workload_percent"{
  type = number
  default = 100
  description = <<EOT
    The amount of workload in percent to scale out. Similar to scaling_adjustment, but we only support percent.
    https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/autoscaling_policy#scaling_adjustment
  EOT
}
variable "scale_out_cooldown"{
  type = number
  default = 0
  description = <<EOT
    Amount of time, in seconds, after a scale out activity completes before another scale out activity can start.
    You will need to figure our how long does it take for the task to start and give it some buffer.
    Default 0 so that in the terraform codes it will take 2*var.health_check_grace_period_seconds
    https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/autoscaling_policy#scale_out_cooldown
  EOT
}

variable "scale_in_threshold"{
  type = number
  default = 20
  description = <<EOT
    Target value for the metric to trigger, e.g. Average CPUUtilization < 20%
    https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm#target_threshold
  EOT
}
variable "scale_in_evaluation_periods"{
  type = number
  default = 10
  description = <<EOT
    The number of periods over which data is compared to the specified threshold, 1 datapoint is 1 minutes.
    https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm#evaluation_periods
  EOT
}
variable "scale_in_workload_percent"{
  type = number
  default = -40
  description = <<EOT
    The amount of workload in percent to scale out. Similar to scaling_adjustment, but we only support percent.
    https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/autoscaling_policy#scaling_adjustment
  EOT
}
variable "scale_in_cooldown"{
  type = number
  default = 0
  description = <<EOT
    Amount of time, in seconds, after a scale in activity completes before another scale in activity can start.
    You will need to figure our how long does it take for the task to start and give it some buffer.
    Default 0 so that in the terraform codes it will take 2*var.health_check_grace_period_seconds
    https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/appautoscaling_policy#scale_in_cooldown
  EOT
}