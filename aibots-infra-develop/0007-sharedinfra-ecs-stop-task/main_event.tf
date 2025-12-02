# resource "aws_cloudwatch_event_rule" "project" {
#   name        = "${local.cwevent_name}"
#   description = "stop task on latest image push to auto restart"

#   tags = merge(
#     { "Name" = "${local.cwevent_name}" },
#     local.tags
#   )

#   event_pattern = jsonencode( {
#     source      = ["aws.ecr"]
#     detail-type = [ "ECR Image Action", ]
#     detail      = {
#       action-type = [ "PUSH",    ]
#       image-tag   = [ "latest",  ]
#       result      = [ "SUCCESS", ]
#     }
#   } )
# }

# resource "aws_cloudwatch_event_target" "lambda" {
#   rule      = aws_cloudwatch_event_rule.project.name
#   target_id = "InvokeLambda"
#   arn       = module.simple_lambda.lambda_function.arn
# }

# ################################################################################
# # allows cloudwatch event to trigger
# resource "aws_lambda_permission" "cloudwatch_event" {
#   statement_id  = "AllowExecutionFromCloudWatchEvent"
#   action        = "lambda:InvokeFunction"
#   function_name = module.simple_lambda.lambda_function.function_name
#   principal     = "events.amazonaws.com"
#   # source_arn    = aws_cloudwatch_event_rule.project.arn
#   source_arn    = "arn:aws:events:ap-southeast-1:003031427344:rule/cwevent-uatezapp-sharedsvc-nous-api"
# }