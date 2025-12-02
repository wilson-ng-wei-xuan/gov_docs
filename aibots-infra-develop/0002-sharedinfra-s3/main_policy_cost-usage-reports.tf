data "aws_iam_policy_document" "cost-usage-reports" {
  # Deny when not using HTTPS, im requirement
  statement {
    sid       = "Stmt1335892150622"
    effect    = "Allow"
    resources = ["arn:aws:s3:::${local.s3_prefix}-${terraform.workspace}${var.zone}-${var.project_code}-${data.aws_caller_identity.current.account_id}-cost-usage-reports"]

    actions = [
      "s3:GetBucketAcl",
      "s3:GetBucketPolicy",
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = ["arn:aws:cur:us-east-1:${data.aws_caller_identity.current.account_id}:definition/*"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = ["${data.aws_caller_identity.current.account_id}"]
    }

    principals {
      type        = "Service"
      identifiers = ["billingreports.amazonaws.com"]
    }
  }

  statement {
    sid       = "Stmt1335892526596"
    effect    = "Allow"
    resources = ["arn:aws:s3:::${local.s3_prefix}-${terraform.workspace}${var.zone}-${var.project_code}-${data.aws_caller_identity.current.account_id}-cost-usage-reports/*"]
    actions   = ["s3:PutObject"]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = ["arn:aws:cur:us-east-1:${data.aws_caller_identity.current.account_id}:definition/*"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = ["${data.aws_caller_identity.current.account_id}"]
    }

    principals {
      type        = "Service"
      identifiers = ["billingreports.amazonaws.com"]
    }
  }
}