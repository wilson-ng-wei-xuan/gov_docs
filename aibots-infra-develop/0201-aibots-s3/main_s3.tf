module "s3" {
  source = "../modules/s3"

  bucket = "${data.aws_caller_identity.current.account_id}-${var.project_desc}"
  aws_s3_bucket_logging = data.aws_s3_bucket.access-logs-s3.id
  versioning = var.versioning
  force_destroy = var.force_destroy
  bucket_key_enabled = var.bucket_key_enabled

  additional_lifecycle = [ {
    id = "cleanup archive files"
    status = "Enabled"
    filter = {
      prefix = "batch/archive"
    }
    noncurrent_version_expiration = {
      noncurrent_days = 7
      newer_noncurrent_versions = null
    }
    abort_incomplete_multipart_upload = {
      days_after_initiation = 1
    }
    expiration = {
      days = 30
      expired_object_delete_marker = null
    }
  } ]

  # bucket_policy = data.aws_iam_policy_document.aws_log_delivery_write
  tags = local.tags
}

# resource "aws_s3_bucket_lifecycle_configuration" "cleanup_archive" {
#   # Must have bucket versioning enabled first
#   # depends_on = [module.s3.bucket]

#   bucket = module.s3.bucket.id

#   rule {
#     id = "cleanup archive"

#     filter {
#       prefix = "archive/"
#     }

#     noncurrent_version_expiration {
#       noncurrent_days = 7
#       # newer_noncurrent_versions = var.newer_noncurrent_versions
#     }

#     abort_incomplete_multipart_upload {
#       days_after_initiation = 1
#     }

#     expiration {
#       days                         = 0
#       expired_object_delete_marker = true
#     }

#     status = "Enabled"
#   }
# }