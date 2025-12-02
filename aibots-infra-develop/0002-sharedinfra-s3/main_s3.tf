module "s3" {
  for_each  = { for entry in var.buckets: "${entry}" => entry }
  source = "../modules/s3"

  bucket = "${data.aws_caller_identity.current.account_id}-${each.value}"
  aws_s3_bucket_logging = data.aws_s3_bucket.access-logs-s3.id
  versioning = var.versioning
  force_destroy = var.force_destroy
  bucket_key_enabled = var.bucket_key_enabled
  bucket_policy = local.buckets_policy[ index( var.buckets, each.value ) ]

  # noncurrent_days = 7
  # newer_noncurrent_versions = null
  tags = local.tags
}

locals {
  buckets_policy = [
    null,
    data.aws_iam_policy_document.cost-usage-reports,
    data.aws_iam_policy_document.access-logs-elb,
    null,
  ]
}