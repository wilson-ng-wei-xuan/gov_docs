resource "aws_iam_role" "apigw-logger" {
  name        = "${local.role_name}apigw-logger"
  description = "Allows API Gateway to push logs to CloudWatch Logs."

  assume_role_policy = jsonencode(
    {
      Version = "2012-10-17"
      Statement = [
        {
          Action = "sts:AssumeRole"
          Effect = "Allow"
          Principal = {
            Service = "apigateway.amazonaws.com"
          }
        },
      ]
    }
  )

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs",
  ]

  tags = merge(
    { "Name" = "${local.role_name}apigw-logger" },
    local.tags
  )
}