variable "agency_code" {
  type = string
  default = "gvt"
}

variable "dept" {
  type  = string
  default = "dsaid"
}

variable "project_code" {
  type = string
  default = "aibots"
}

variable "project_desc" {
  type = string
  default = "main-api"
}

variable "zone" {
  type = string
  default = "ez"
}

variable "tier" {
  type = string
  default = "app"
}

variable "ops_enddate" {
  type    = string
  default = "dec 2099"
}

#######################################################
## project specific variables
## supply the value in ./environments/project.[env].tfvars
#######################################################
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

variable "task_role_managed_policy_arns" {
  type = list
  default = null
  description = <<EOT
    (Required) This module will create the IAM role for the task.
    Task role is permission for the application, e.g. read files in S3 bucket, SQS, SNS etc.
    Add in the managed_policy_arns needed by your application.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role
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

variable "sso" {
  type = bool
  default = false
}

variable "pub" {
  type = object(
    {
      name  = string
      host  = string
    }
  )
  default = {
    name = "pub"
    host = "api."
  }
  description = <<EOT
    pub_deployment = {
      name : "Suffix of resource name"
      host : "Host name"
    }
  EOT
}

variable "pte" {
  type = object(
    {
      name  = string
      host  = string
    }
  )
  default = {
    name = "pte"
    host = "api."
  }
  description = <<EOT
    pte_deployment = {
      name : "Suffix of resource name"
      host : "Host name"
    }
  EOT
}

variable "path_pattern" {
  type = string
  default = "/"
  description = <<EOT
    Path patterns to match against the request URL.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener_rule#path_pattern
  EOT
}

variable "health_check_interval" {
  type = number
  default = 60
  description = <<EOT
    Approximate amount of time, in seconds, between health checks of an individual target.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group#interval
  EOT
}

variable "health_check_path" {
  type = string
  default = "/heartbeat"
  description = <<EOT
    Destination for the health check request.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group
  EOT
}

variable "certificate_arn" {
  type = list
  description = <<EOT
    The arn of the AWS Certificate Manager.
    You shall provide [] in the var file, if you do not need.
    This is to force you to know what you are deploying.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener_certificate#listener_arn
  EOT
}

variable "capacity_providers" {
  type = string
  default = "FARGATE_SPOT"
  description = <<EOT
    Short name of the capacity provider, choose either FARGATE_SPOT or FARGATE
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_cluster_capacity_providers
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_service
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

variable "retention_in_days" {
  type = number
}

variable "secret_rotation" {
  type = bool
  default = true
  description = <<EOT
    Secret for the JWT hashing.
    Only VPC that has a public front end needs the JWT hashing to track user session.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_rotation
  EOT
}

variable "secret_rotation_schedule_expression" {
  type = string
  description = <<EOT
    The schedule to rotate secrets.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_rotation#schedule_expression
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