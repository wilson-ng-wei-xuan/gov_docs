######################################################################################
module "simple_lambda" {
  count = var.secret_rotation == false ? 0 : 1

  source = "../modules/lambda_secret_rotator_cloudfront"

  # # setting this has no effect as secret_rotator_cloudfront is hardcoded
  # The variables required by your module e.g shown below
  function_name = "${var.project_code}-secret_rotator_cloudfront"
  memory_size = 128
  # https://repost.aws/questions/QU8N6m5gUDS_a-MDNBPO4d9g/cloudfront-endpoint-missing-in-vpc-endpoints
  # https://docs.aws.amazon.com/general/latest/gr/cf_region.html
  # CloudFront does not have endpoints in SG to control plane
  # secret_rotator needs to update the CloudFront public key and key group
  # thus it cannot be in VPC
  security_group_ids = [ ]
  subnet_ids = [ ]
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
  ]
  handler = "lambda_function.lambda_handler"
  timeout = 20
  runtime = local.default_lambda_runtime

  # # Only these are applicable
  layers = [ data.aws_lambda_layer_version.LambdaInsightsExtension.id ]
  secret_arn = aws_secretsmanager_secret.project[0].arn
  retention_in_days = var.retention_in_days
  destination_arn = data.aws_lambda_function.notification.arn

  tags = local.tags
}