# task role is permission for the application, e.g. read files in S3 bucket etc.
resource "aws_iam_role" "task_role" {
  name                = "${local.role_name}-${var.family}-task"
  description         = "ecs task role for ${local.ecs_task_name}-${var.family}"
  
  assume_role_policy  = jsonencode(
    {
      Version   = "2012-10-17"
      Statement = [
        {
          Action    = "sts:AssumeRole"
          Effect    = "Allow"
          Principal = {
            Service = "ecs-tasks.amazonaws.com"
          }
        },
      ]
    }
  )

  managed_policy_arns = var.task_role_managed_policy_arns

  dynamic "inline_policy" {
    for_each = var.task_role_inline_policy
    
    content {
      name     = inline_policy.value.name
      policy = inline_policy.value.policy
    }
  }

  tags = merge(
    { "Name" = "${local.role_name}-${var.family}-task" },
    local.tags,
    var.additional_tags
  )
}

# execution role is permission for the ECS agents, e.g. write to cloudwatch logs.
resource "aws_iam_role" "execution_role" {
  name                = "${local.role_name}-${var.family}-execution"
  description         = "ecs execution role for ${local.ecs_task_name}-${var.family}"

  assume_role_policy  = jsonencode(
    {
      Version   = "2012-10-17"
      Statement = [
        {
          Action    = "sts:AssumeRole"
          Effect    = "Allow"
          Principal = {
            Service = "ecs-tasks.amazonaws.com"
          }
        },
      ]
    }
  )

  force_detach_policies = false
  max_session_duration  = 3600
  path          = "/"

  tags = merge(
    { "Name" = "${local.role_name}-${var.family}-execution" },
    local.tags,
    var.additional_tags
  )

  managed_policy_arns = var.execution_role_managed_policy_arns

  inline_policy {
    name   = "${local.policy_name}-${var.family}-execution"
    policy = data.aws_iam_policy_document.execution_role_combined.json
  }
}

data "aws_iam_policy_document" "execution_role_combined" {
  source_policy_documents = concat(
    [ data.aws_iam_policy_document.execution_role_default.json ],
    length(var.secretsmanager_secret_arn) == 0 ? [] : [ data.aws_iam_policy_document.execution_role_secret.json ],
  )
}

data "aws_iam_policy_document" "execution_role_secret" {
  statement {
    actions = [ 
      "secretsmanager:GetSecretValue"
    ]
    resources = var.secretsmanager_secret_arn
    effect = "Allow"
  }
}

data "aws_iam_policy_document" "execution_role_default" {
  statement {
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage"
    ]
    resources = var.ecr_repository_arn
    effect = "Allow"
  }

  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
#                aws_cloudwatch_log_group.cloudwatch_log_group.arn,
        "${module.cloudwatch_log_group.cloudwatch_log_group.arn}:log-stream:*",
    ]
    effect = "Allow"
  }

  statement {
    actions = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
    effect = "Allow"
  }
}
