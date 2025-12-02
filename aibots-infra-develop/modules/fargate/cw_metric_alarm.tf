resource "aws_cloudwatch_metric_alarm" "scaleout" {
  count = var.cw_alarm_sns_topic_arn == null ? 0 : 1
  alarm_name                = "${local.alarm_name}-${var.family}-scaleout"
  actions_enabled           = true

  alarm_actions             = [var.cw_alarm_sns_topic_arn, aws_appautoscaling_policy.scaleout[count.index].arn]
  ok_actions                = [var.cw_alarm_sns_topic_arn]
  insufficient_data_actions = [var.cw_alarm_sns_topic_arn]

  namespace                 = "AWS/ECS"
  dimensions                = {
    "ClusterName" = aws_ecs_cluster.ecs_cluster.name
    "ServiceName"  = aws_ecs_service.ecs_service.name
  }

  metric_name               = "CPUUtilization"
  statistic                 = "Average"
  comparison_operator       = "GreaterThanThreshold"
  threshold                 = var.scale_out_threshold
  period                    = 60
  evaluation_periods        = var.scale_out_evaluation_periods
  treat_missing_data        = "breaching"
  datapoints_to_alarm       = var.scale_out_evaluation_periods

  tags = merge(
    local.tags,
    {
      "Name" = "${local.alarm_name}-${var.family}-scaleout",
    }
  )
}


resource "aws_cloudwatch_metric_alarm" "scalein" {
  count = var.cw_alarm_sns_topic_arn == null ? 0 : 1
  alarm_name                = "${local.alarm_name}-${var.family}-scalein"
  actions_enabled           = true

  namespace                 = "AWS/ECS"
  dimensions                = {
    "ClusterName" = aws_ecs_cluster.ecs_cluster.name
    "ServiceName"  = aws_ecs_service.ecs_service.name
  }

  metric_name               = "CPUUtilization"
  statistic                 = "Average"
  comparison_operator       = "LessThanThreshold"
  threshold                 = var.scale_in_threshold
  period                    = 60
  evaluation_periods        = var.scale_in_evaluation_periods
  treat_missing_data        = "breaching"
  datapoints_to_alarm       = var.scale_in_evaluation_periods

  alarm_actions             = [var.cw_alarm_sns_topic_arn, aws_appautoscaling_policy.scalein[count.index].arn]
  ok_actions                = [var.cw_alarm_sns_topic_arn]
  insufficient_data_actions = [var.cw_alarm_sns_topic_arn]

  tags = merge(
    local.tags,
    {
      "Name" = "${local.alarm_name}-${var.family}-scalein",
    }
  )
}


# resource "aws_cloudwatch_metric_alarm" "CPUUtilization" {
#   count = var.cw_alarm_sns_topic_arn == null ? 0 : 1
#   alarm_name                = "${local.alarm_name}-${var.family}-CPUUtilization"
#   actions_enabled           = true

#   namespace                 = "AWS/ECS"
#   dimensions                = {
#     "ClusterName" = aws_ecs_cluster.ecs_cluster.name
#     "ServiceName"  = aws_ecs_service.ecs_service.name
#   }

#   metric_name               = "CPUUtilization"
#   statistic                 = "Maximum"
#   comparison_operator       = "GreaterThanThreshold"
#   threshold                 = 60
#   period                    = 60
#   evaluation_periods        = 2
#   treat_missing_data        = "breaching"
#   datapoints_to_alarm       = 2

#   alarm_actions             = [var.cw_alarm_sns_topic_arn]
#   ok_actions                = [var.cw_alarm_sns_topic_arn]
#   insufficient_data_actions = [var.cw_alarm_sns_topic_arn]

#   tags = merge(
#     local.tags,
#     {
#       "Name" = "${local.alarm_name}-${var.family}-CPUUtilization",
#     }
#   )
# }

# resource "aws_cloudwatch_metric_alarm" "MemoryUtilization" {
#   count = var.cw_alarm_sns_topic_arn == null ? 0 : 1
#   alarm_name                = "${local.alarm_name}-${var.family}-MemoryUtilization"
#   actions_enabled           = true

#   namespace                 = "AWS/ECS"
#   dimensions                = {
#     "ClusterName" = aws_ecs_cluster.ecs_cluster.name
#     "ServiceName"  = aws_ecs_service.ecs_service.name
#   }

#   metric_name               = "MemoryUtilization"
#   statistic                 = "Maximum"
#   comparison_operator       = "GreaterThanThreshold"
#   threshold                 = 90
#   period                    = 60
#   evaluation_periods        = 2
#   treat_missing_data        = "breaching"
#   datapoints_to_alarm       = 2

#   alarm_actions             = [var.cw_alarm_sns_topic_arn]
#   ok_actions                = [var.cw_alarm_sns_topic_arn]
#   insufficient_data_actions = [var.cw_alarm_sns_topic_arn]

#   tags = merge(
#     local.tags,
#     {
#       "Name" = "${local.alarm_name}-${var.family}-MemoryUtilization",
#     }
#   )
# }