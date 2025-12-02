data "aws_s3_bucket" "statefile" {
  bucket = "${local.s3_prefix}-${var.agency_code}-${var.dept}-${data.aws_caller_identity.current.account_id}-terraform-statefile"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sse" {
  bucket = data.aws_s3_bucket.statefile.id
  rule {
    bucket_key_enabled = true

    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "s3_bucket_versioning" {
  bucket = data.aws_s3_bucket.statefile.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_acl" "bucket_acl" {
  depends_on = [aws_s3_bucket_ownership_controls.bucket_ownership_controls]
  bucket = data.aws_s3_bucket.statefile.id
  acl    = "private"
}

resource "aws_s3_bucket_public_access_block" "public_access_block" {
  bucket = data.aws_s3_bucket.statefile.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "bucket_ownership_controls" {
  bucket = data.aws_s3_bucket.statefile.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

data "aws_iam_policy_document" "combined" {
  source_policy_documents = concat(
    [ data.aws_iam_policy_document.deny_non_https.json ],
    # var.bucket_policy == null? [] : [ var.bucket_policy.json ],
  )
}

resource "aws_s3_bucket_policy" "bucket_policy" {
  bucket = data.aws_s3_bucket.statefile.id
  policy = data.aws_iam_policy_document.combined.json
}

data "aws_iam_policy_document" "deny_non_https" {
  # Deny when not using HTTPS, im requirement
  statement {
    effect = "Deny"
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    actions = [
      "s3:*"
    ]
    condition {
    # https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_condition_operators.html
      test = "Bool"
      variable = "aws:SecureTransport"
      values = [
        false
      ]
    }
    resources = [
      "arn:aws:s3:::${data.aws_s3_bucket.statefile.id}",
      "arn:aws:s3:::${data.aws_s3_bucket.statefile.id}/*",
    ]
  }
}

resource "aws_s3_bucket_logging" "logging" {
  # S3 buckets should have logging enabled, CS 1.6/S4d, CS 1.3/S2c
  bucket = data.aws_s3_bucket.statefile.id

  target_bucket = data.aws_s3_bucket.access-logs-s3.id
  target_prefix = ""
  target_object_key_format {
    partitioned_prefix {
      partition_date_source = "DeliveryTime"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "versioning-bucket-config" {
  # Must have bucket versioning enabled first
  depends_on = [aws_s3_bucket_versioning.s3_bucket_versioning]

  bucket = data.aws_s3_bucket.statefile.id

  dynamic "rule" {
    for_each = local.default_lifecycle
    
    content {
      id = rule.value.id
      status = rule.value.status

      filter {
        # prefix = try( rule.value.filter.prefix, null )
        prefix = rule.value.filter.prefix
      }

      noncurrent_version_expiration {
        noncurrent_days = rule.value.noncurrent_version_expiration.noncurrent_days
        newer_noncurrent_versions = rule.value.noncurrent_version_expiration.newer_noncurrent_versions
      }

      abort_incomplete_multipart_upload {
        days_after_initiation = rule.value.abort_incomplete_multipart_upload.days_after_initiation
      }

      expiration {
        days = rule.value.expiration.days
        expired_object_delete_marker = rule.value.expiration.expired_object_delete_marker
      }
    }
  }
}

locals {
  default_lifecycle = [ {
    id = "default cleanup deleted files"
    status = "Enabled"
    filter = {
      prefix = null
    }
    noncurrent_version_expiration = {
      noncurrent_days = 7
      newer_noncurrent_versions = null
    }
    abort_incomplete_multipart_upload = {
      days_after_initiation = 1
    }
    expiration = {
      days = null
      expired_object_delete_marker = true
    }
  } ]
}