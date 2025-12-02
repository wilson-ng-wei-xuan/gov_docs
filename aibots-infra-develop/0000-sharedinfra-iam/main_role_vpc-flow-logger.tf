resource "aws_iam_role" "vpc-flow-logger" {
  name        = "${local.role_name}vpc-flow-logger"
  description = "Allows vpc flow logs."

  assume_role_policy = jsonencode(
    {
      Statement = [
        {
          Action = "sts:AssumeRole"
          Effect = "Allow"
          Principal = {
            Service = "vpc-flow-logs.amazonaws.com"
          }
        },
      ]
      Version = "2012-10-17"
    }
  )

  inline_policy {
    name   = "flowLogsPolicy"
    policy = data.aws_iam_policy_document.vpc-flow-logger.json
  }

  tags = merge(
    { "Name" = "${local.role_name}vpc-flow-logger" },
    local.tags
  )
}

data "aws_iam_policy_document" "vpc-flow-logger" {
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
    ]

    resources = ["*"]
  }
}