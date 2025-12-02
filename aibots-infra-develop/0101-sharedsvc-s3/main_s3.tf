module "s3" {
  for_each  = { for entry in var.buckets: "${entry}" => entry }
  source = "../modules/s3"

  bucket = "${data.aws_caller_identity.current.account_id}-${each.value}"
  aws_s3_bucket_logging = data.aws_s3_bucket.access-logs-s3.id
  versioning = var.versioning
  force_destroy = var.force_destroy
  bucket_key_enabled = var.bucket_key_enabled
  # bucket_policy = data.aws_iam_policy_document.aws_log_delivery_write

  # noncurrent_days = 7
  # newer_noncurrent_versions = null
  tags = local.tags
}