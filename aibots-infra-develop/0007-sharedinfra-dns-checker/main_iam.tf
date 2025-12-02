# resource "aws_lambda_permission" "event_bridge" {
#   statement_id = "InvokeLambdaFunction"
#   action = "lambda:InvokeFunction"
#   function_name = module.simple_lambda.lambda_function.function_name
#   principal = "events.amazonaws.com"
#   source_arn = "arn:aws:scheduler:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:schedule/default/${module.simple_lambda.lambda_function.function_name}-*"
# }


resource "aws_iam_role" "event_bridge" {
  count = terraform.workspace == "sit" ? 1 : 0 # only deploy on SIT

  name        = "${local.role_name}-event_bridge"
  description = "Allows Event Bridge to trigger lambda."

  assume_role_policy = jsonencode(
    {
      Statement = [
        {
          Action = "sts:AssumeRole"
          Effect = "Allow"
          Principal = {
            Service = "scheduler.amazonaws.com"
          }
        },
      ]
      Version = "2012-10-17"
    }
  )

  managed_policy_arns = ["arn:aws:iam::aws:policy/service-role/AWSLambdaRole"]
  # inline_policy {
  #   name   = "AllowPermissions"
  #   policy = data.aws_iam_policy_document.event_bridge.json
  # }

  tags = merge(
    { "Name" = "${local.role_name}-event_bridge" },
    local.tags
  )
}

# data "aws_iam_policy_document" "event_bridge" {
#   statement {
#     sid = "CloudWatchEventsFullAccess"
#     effect = "Allow"

#     actions = [
#       "logs:CreateLogGroup",
#     ]

#     resources = ["*"]
#   }

#   # statement {
#   #   sid = "IAMPassRoleForCloudWatchEvents"
#   #   effect = "Allow"

#   #   actions = [
#   #     "iam:PassRole",
#   #   ]

#   #   resources = ["arn:aws:iam::*:role/AWS_Events_Invoke_Targets"]
#   # }
# }