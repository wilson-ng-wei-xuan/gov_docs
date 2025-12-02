module "s3-cloudfront" {
  source = "../modules/s3"

  bucket = "${data.aws_caller_identity.current.account_id}-cloudfront"
  aws_s3_bucket_logging = data.aws_s3_bucket.access-logs-s3.id
  versioning = var.versioning
  force_destroy = var.force_destroy
  bucket_key_enabled = var.bucket_key_enabled
  bucket_policy = data.aws_iam_policy_document.allow_cloudfront

  # noncurrent_days = 7
  # newer_noncurrent_versions = null
  tags = local.tags
}

data "aws_iam_policy_document" "allow_cloudfront" {
  # Deny when not using HTTPS, im requirement
  statement {
    sid = "AllowCloudFrontServicePrincipal"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }
    actions = [
      "s3:GetObject"
    ]
    resources = [
      "arn:aws:s3:::${module.s3-cloudfront.bucket.id}/*",
    ]
    condition {
      variable = "AWS:SourceArn"
      test     = "StringEquals"
      values   = [ aws_cloudfront_distribution.project.arn ]
    }
  }
}
