module "s3" {
  count = terraform.workspace == "sit" ? 1 : 0 # only deploy on SIT

  source = "../modules/s3"

  bucket = "${data.aws_caller_identity.current.account_id}-${var.project_desc}"
  aws_s3_bucket_logging = data.aws_s3_bucket.access-logs-s3.id
  versioning = var.versioning
  force_destroy = var.force_destroy
  bucket_key_enabled = var.bucket_key_enabled
  # bucket_policy = data.aws_iam_policy_document.aws_log_delivery_write

  additional_lifecycle = [ {
    id = "cleanup zip files"
    status = "Enabled"
    filter = {
      prefix = "dns_past_results/"
    }
    noncurrent_version_expiration = {
      noncurrent_days = 180
      newer_noncurrent_versions = null
    }
    abort_incomplete_multipart_upload = {
      days_after_initiation = 1
    }
    expiration = {
      days = 180
      expired_object_delete_marker = null
    }
  } ]
  # noncurrent_days = 7
  # newer_noncurrent_versions = null
  tags = local.tags
}