resource "aws_cloudwatch_metric_alarm" "cloudwatch_metric_alarm" {
  alarm_name                = "${local.cw_alarm_name}"
  actions_enabled           = true

  metric_name               = "UnhealthyStateRouting"
  namespace                 = "AWS/ApplicationELB"
  dimensions                = {
    "LoadBalancer" = data.aws_lb.ezingressalb.arn_suffix
    "TargetGroup"  = aws_lb_target_group.lb_target_group.arn_suffix
  }

  statistic                 = "Maximum"
  comparison_operator       = "GreaterThanThreshold"
  threshold                 = 0
  period                    = 60
  evaluation_periods        = 1
  treat_missing_data        = "breaching"
  datapoints_to_alarm       = 1

  alarm_actions             = [aws_sns_topic.sns_topic.arn]
  ok_actions                = [aws_sns_topic.sns_topic.arn]
  insufficient_data_actions = [aws_sns_topic.sns_topic.arn]
  tags                      = merge(
    { "Name" = "${local.cw_alarm_name}" },
    local.context_tags
  )
}

resource "aws_sns_topic" "sns_topic" {
  name            = "${local.sns_name}"

  tags = merge(
    { "Name" = "${local.sns_name}" },
    local.context_tags
  )

  delivery_policy = <<EOF
{
  "http": {
    "defaultHealthyRetryPolicy": {
      "minDelayTarget": 20,
      "maxDelayTarget": 20,
      "numRetries": 3,
      "numMaxDelayRetries": 0,
      "numNoDelayRetries": 0,
      "numMinDelayRetries": 0,
      "backoffFunction": "linear"
    },
    "disableSubscriptionOverrides": false,
    "defaultThrottlePolicy": {
      "maxReceivesPerSecond": 1
    }
  }
}
EOF
}
