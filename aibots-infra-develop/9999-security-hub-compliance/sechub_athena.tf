resource "aws_athena_workgroup" "compliance" {
  name = "IM_Compliance"
  description = "Use this workgroup for your athena query."

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${data.aws_s3_bucket.athena.bucket}/output/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }

  tags = merge(
    local.tags,
    {
      "Name" = "default",
      "Project-Code" = "sharedinfra",
      "Project-Desc" = "athena"
    }
  )

}