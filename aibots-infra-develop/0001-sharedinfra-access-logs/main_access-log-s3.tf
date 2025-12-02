module "access-logs-s3" {
  # version = "~>2.0"
  source = "../modules/s3"
  bucket = "${data.aws_caller_identity.current.account_id}-${var.project_desc}-s3"
  aws_s3_bucket_logging = null
  versioning = var.versioning
  force_destroy = var.force_destroy
  bucket_key_enabled = var.bucket_key_enabled
  bucket_policy = data.aws_iam_policy_document.allow_s3_logging

  # noncurrent_days = 7
  # newer_noncurrent_versions = null
  tags = local.tags
}

data "aws_iam_policy_document" "allow_s3_logging" {
  # Deny when not using HTTPS, im requirement
  statement {
    sid = "S3PolicyStmt-DO-NOT-MODIFY-1701142409232"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["logging.s3.amazonaws.com"]
    }
    actions = [
      "s3:PutObject"
    ]
    resources = [
      "arn:aws:s3:::${module.access-logs-s3.bucket.id}/*",
    ]
  }
}

resource "aws_s3_bucket_acl" "log_bucket_acl" {
  depends_on = [ module.access-logs-s3.aws_s3_bucket_ownership_controls ]

  bucket = module.access-logs-s3.bucket.id
  acl    = "log-delivery-write"
}