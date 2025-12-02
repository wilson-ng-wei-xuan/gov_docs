locals {
  # prefix "-" to bucket_name if it does not start with "-"
  bucket_name = substr( var.bucket, 0, 1) == "-" ? var.bucket : "-${var.bucket}"
  # bucket = substr( "${local.s3_prefix}-${var.tags.Environment}${var.tags.Zone}${var.tags.Tier}-${var.tags.Project-Code}${local.bucket_name}", 0, 63)
  bucket = substr( "${local.s3_prefix}-${var.tags.Environment}${var.tags.Zone}${local.tier_name}-${var.tags.Project-Code}${local.bucket_name}", 0, 63)
}

resource "aws_s3_bucket" "the_bucket" {
  bucket        = local.bucket
  force_destroy = var.force_destroy

  # checkov:skip=CKV_AWS_144: "Cross Region Replication is not mandatory"
  # checkov:skip=CKV_AWS_145: "KMS encryption is not mandatory for now."
  # checkov:skip=CKV_AWS_18: "S3 Access Logging is skipped for now."

  tags = merge(     
    local.tags,
    var.additional_tags,
    { "Name" = local.bucket }
  )
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sse" {
  bucket = aws_s3_bucket.the_bucket.id
  rule {
    bucket_key_enabled = var.bucket_key_enabled

    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "s3_bucket_versioning" {
  bucket = aws_s3_bucket.the_bucket.id
  versioning_configuration {
    status = var.versioning
  }
}

resource "aws_s3_bucket_acl" "bucket_acl" {
  depends_on = [aws_s3_bucket_ownership_controls.bucket_ownership_controls]
  bucket = aws_s3_bucket.the_bucket.id
  acl    = "private"
}

resource "aws_s3_bucket_public_access_block" "public_access_block" {
  bucket = aws_s3_bucket.the_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "bucket_ownership_controls" {
  bucket = aws_s3_bucket.the_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

data "aws_iam_policy_document" "combined" {
  source_policy_documents = concat(
    [ data.aws_iam_policy_document.deny_non_https.json ],
    var.bucket_policy == null? [] : [ var.bucket_policy.json ],
  )
}

resource "aws_s3_bucket_policy" "bucket_policy" {
  bucket = aws_s3_bucket.the_bucket.id
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
      "arn:aws:s3:::${aws_s3_bucket.the_bucket.id}",
      "arn:aws:s3:::${aws_s3_bucket.the_bucket.id}/*",
    ]
  }
}

resource "aws_s3_bucket_logging" "logging" {
  count = var.aws_s3_bucket_logging == null ? 0 : 1
  # S3 buckets should have logging enabled, CS 1.6/S4d, CS 1.3/S2c
  bucket = aws_s3_bucket.the_bucket.id

  target_bucket = var.aws_s3_bucket_logging
  # target_prefix = "${aws_s3_bucket.the_bucket.id}/"
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

  bucket = aws_s3_bucket.the_bucket.id

  dynamic "rule" {
    for_each = local.rules
    
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
  rules = var.keep_default_lifecycle == true ? concat( local.default_lifecycle, var.additional_lifecycle ) : var.additional_lifecycle

  default_lifecycle = [ {
    id = "default cleanup deleted files"
    status = "Enabled"
    filter = {
      prefix = null
    }
    noncurrent_version_expiration = {
      noncurrent_days = var.noncurrent_days
      newer_noncurrent_versions = var.newer_noncurrent_versions
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