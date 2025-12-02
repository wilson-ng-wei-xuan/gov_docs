resource "aws_iam_role" "task_role" {
  name                = "${local.role_name}-task"
  description         = "ecs task role for ${local.role_name}"
  
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

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    "arn:aws:iam::aws:policy/AmazonSESFullAccess",
    "arn:aws:iam::aws:policy/AmazonSQSFullAccess",
    "arn:aws:iam::aws:policy/SecretsManagerReadWrite",
  ]

  tags = merge(
    { "Name" = "${local.role_name}-task" },
    local.tags
  )
}

resource "aws_iam_role" "execution_role" {
  name                = "${local.role_name}-execution"
  description         = "ecs execution role for ${local.role_name}"

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
    { "Name" = "${local.role_name}-execution" },
    local.tags
  )

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
  ]

  inline_policy {
    name   = "${local.policy_name}-execution"

    policy = jsonencode(
      {
        Version = "2012-10-17",
        Statement = [
          {
            "Effect": "Allow",
            "Action": [
              "secretsmanager:GetSecretValue"
            ],
            "Resource": [
              "${aws_secretsmanager_secret.secretsmanager_secret.arn}"
            ]
          },
          {
            Action = [
              "ecr:BatchCheckLayerAvailability",
              "ecr:GetDownloadUrlForLayer",
              "ecr:BatchGetImage"
            ],
            Resource = aws_ecr_repository.ecr_repository.arn,
            Effect = "Allow"
          },
          {
            Action = [
              "logs:CreateLogStream",
              "logs:PutLogEvents",
            ],
            Resource = [
#                aws_cloudwatch_log_group.cloudwatch_log_group.arn,
                "${aws_cloudwatch_log_group.cloudwatch_log_group.arn}:log-stream:*",
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
  }
}