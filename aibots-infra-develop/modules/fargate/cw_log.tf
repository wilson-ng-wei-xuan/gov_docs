module "cloudwatch_log_group" {
  # source = "sgts.gitlab-dedicated.com/wog/svc-iac-layer-1-simple-s3-private-bucket/aws"
  # version = "~>2.0"
  source  = "../cloudwatch_log_group"
  name    = "/aws/ecs-task/${local.ecs_task_name}-${var.family}"
  
  retention_in_days	= "${var.retention_in_days}"
  destination_arn = "${var.destination_arn}"
  filter_pattern = "${var.filter_pattern}"

  tags = var.tags
  additional_tags = merge(
    { "Name" = "/aws/ecs-task/${local.cw_log_name}-${var.family}" },
    var.additional_tags
  )
}
