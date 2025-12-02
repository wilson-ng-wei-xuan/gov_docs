resource "aws_lambda_permission" "s3_bucket_notification" {
  count = terraform.workspace == "sit" ? 1 : 0 # only deploy on SIT

  statement_id = "AllowExecutionFromS3Bucket"
  action = "lambda:InvokeFunction"
  function_name = module.simple_lambda[0].lambda_function.function_name
  principal = "s3.amazonaws.com"
  source_arn = module.s3[0].bucket.arn
}

resource "aws_s3_bucket_notification" "s3_bucket_notification" {
  count = terraform.workspace == "sit" ? 1 : 0 # only deploy on SIT

  bucket = module.s3[0].bucket.id

  eventbridge = true

  lambda_function {
    id = module.simple_lambda[0].lambda_function.function_name
    lambda_function_arn = module.simple_lambda[0].lambda_function.arn
    events = ["s3:ObjectCreated:*"]
    filter_prefix = ""
    filter_suffix = ".json"
  }

  depends_on = [ aws_lambda_permission.s3_bucket_notification[0] ]
}