data "aws_kms_key" "aws-s3" {
  key_id = "alias/aws/s3"
}

resource "aws_iam_role" "analytics" {
  name               = "${local.role_name}-analytics"
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json

  tags = merge(
    { "Name" = "${local.role_name}-analytics" },
    local.tags
  )
}

data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    # Allow root to assume the role, this allows us to permit the role to delegate itself
    principals {
      type        = "AWS"
      identifiers = [
        "arn:aws:iam::414351767826:role/unity-catalog-prod-UCMasterRole-14S5ZJVKOTYTL",
        # you cannot use this as it will end up circular referencing.
        # "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${local.role_name}-analytics"
        # you cannot use wildcard for roles.
        # "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/*-analytics"
        # you can only minimally restrict to within your own account.
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      ]
    }
    condition {
      test     = "StringEquals"
      variable = "sts:ExternalId"
      values   = [ "a674506f-d79f-4645-908c-da172e7eae9e" ]
    }

  }
}

resource "aws_iam_role_policy" "analytics" {
  name    = "AllowPermissions"
  role    = aws_iam_role.analytics.id
  policy  = data.aws_iam_policy_document.role_policy.json
}

data "aws_iam_policy_document" "role_policy" {
  statement {
    effect    = "Allow"
    actions   = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
      "s3:GetBucketLocation"
    ]
    # Allow root to assume the role, this allows us to permit the role to delegate itself
    resources = [
      "${module.s3["analytics"].bucket.arn}/*",
      module.s3["analytics"].bucket.arn
    ]
  }

  statement {
    effect    = "Allow"
    actions   = [
      "kms:Decrypt",
      "kms:Encrypt",
      "kms:GenerateDataKey*"
    ]
    # Allow root to assume the role, this allows us to permit the role to delegate itself
    resources = [
      data.aws_kms_key.aws-s3.arn
    ]
  }

  statement {
    effect    = "Allow"
    actions   = [
      "sts:AssumeRole"
    ]
    # Allow root to assume the role, this allows us to permit the role to delegate itself
    resources = [
      aws_iam_role.analytics.arn
    ]
  }
}