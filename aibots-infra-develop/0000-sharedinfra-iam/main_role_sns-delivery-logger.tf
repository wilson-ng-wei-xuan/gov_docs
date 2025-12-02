resource "aws_iam_role" "sns-delivery" {
  name        = "${local.role_name}sns-delivery"
  description = "Allows sns status delivery logging."

  assume_role_policy = jsonencode(
    {
      Statement = [
        {
          Action = "sts:AssumeRole"
          Effect = "Allow"
          Principal = {
            Service = "sns.amazonaws.com"
          }
        },
      ]
      Version = "2012-10-17"
    }
  )

  inline_policy {
    name   = "flowLogsPolicy"
    policy = data.aws_iam_policy_document.sns-delivery.json
  }

  tags = merge(
    { "Name" = "${local.role_name}sns-delivery" },
    local.tags
  )
}

data "aws_iam_policy_document" "sns-delivery" {
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:PutMetricFilter",
      "logs:PutRetentionPolicy"
    ]

    resources = ["*"]
  }
}