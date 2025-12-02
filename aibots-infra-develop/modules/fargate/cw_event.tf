locals {
  repository-name = flatten(
    [for ecr_arn in var.ecr_repository_arn :
      split("/", ecr_arn)[ length( split("/", ecr_arn) )-1 ]
    ]
  )
}

resource "aws_cloudwatch_event_rule" "fargate_stop_task" {
  count = var.ecs_stop_task == null ? 0 : 1

  name        = "${local.cwevent_name}-${var.family}"
  description = "Restart fargate task ${var.family} when ${ join( ", ", local.repository-name ) } is pushed successfully."

  # event_pattern = jsonencode({
  #   detail-type = [
  #     "AWS Console Sign In via CloudTrail"
  #   ]
  # })
  event_pattern = jsonencode({
    "source": ["aws.ecr"],
    "detail-type": ["ECR Image Action"],
    "detail": {
      "action-type": ["PUSH"],
      "result": ["SUCCESS"],
      "repository-name": local.repository-name,
      "image-tag": ["latest"]
    }
  })

  tags = merge(
    { "Name" = "${local.cwevent_name}-${var.family}" },
    local.tags,
    var.additional_tags
  )
}

resource "aws_cloudwatch_event_target" "lambda" {
  count = var.ecs_stop_task == null ? 0 : 1

  rule      = aws_cloudwatch_event_rule.fargate_stop_task[0].name
  target_id = "InvokeLambda"
  arn       = var.ecs_stop_task.arn
  input     = jsonencode({
    cluster       = aws_ecs_cluster.ecs_cluster.arn
    family        = aws_ecs_task_definition.ecs_task_definition.family
    serviceName   = aws_ecs_service.ecs_service.name
    desiredStatus = "RUNNING"
  })
}

################################################################################
# allows cloudwatch event to trigger
resource "aws_lambda_permission" "cloudwatch_event" {
  count = var.ecs_stop_task == null ? 0 : 1

  statement_id  = aws_cloudwatch_event_rule.fargate_stop_task[0].name
  action        = "lambda:InvokeFunction"
  function_name = var.ecs_stop_task.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.fargate_stop_task[0].arn
}