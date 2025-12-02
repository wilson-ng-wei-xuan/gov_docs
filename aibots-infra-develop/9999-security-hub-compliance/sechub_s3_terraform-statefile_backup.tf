data "aws_kms_key" "backup" {
  key_id = "alias/aws/backup"
}
################################################################################
resource "aws_backup_vault" "backup" {
  name        = local.backup_vault_name
  kms_key_arn = data.aws_kms_key.backup.arn
  tags        = merge( {"Name": local.backup_vault_name}, local.tags )
}

data "aws_iam_policy_document" "backup-vault" {
  statement {
    effect = "Deny"

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    actions = [
      "backup:DeleteRecoveryPoint"
    ]

    resources = [aws_backup_vault.backup.arn]
  }
}

resource "aws_backup_vault_policy" "backup" {
  backup_vault_name = aws_backup_vault.backup.name
  policy            = data.aws_iam_policy_document.backup-vault.json
}
################################################################################
resource "aws_backup_plan" "backup" {
  name = local.backup_plan_name
  tags = local.tags

  rule {
    rule_name                = "daily"
    completion_window        = 120
    enable_continuous_backup = false
    recovery_point_tags      = {}
    target_vault_name = aws_backup_vault.backup.name
    schedule                 = "cron(0 20 * * ? *)"
    start_window             = 60

    lifecycle {
      delete_after                              = 14
      opt_in_to_archive_for_supported_resources = false
      cold_storage_after                        = 0
    }
  }

  # rule {
  #   rule_name                = "weekly"
  #   completion_window        = 120
  #   enable_continuous_backup = false
  #   recovery_point_tags      = {}
  #   target_vault_name = aws_backup_vault.backup.name
  #   schedule                 = "cron(0 20 ? * 1 *)"
  #   start_window             = 60

  #   lifecycle {
  #     delete_after                              = 28
  #     opt_in_to_archive_for_supported_resources = false
  #     cold_storage_after                        = 0
  #   }
  # }

  # rule {
  #   rule_name                = "monthly"
  #   completion_window        = 120
  #   enable_continuous_backup = false
  #   recovery_point_tags      = {}
  #   target_vault_name = aws_backup_vault.backup.name
  #   schedule                 = "cron(0 20 1 * ? *)"
  #   start_window             = 60

  #   lifecycle {
  #     delete_after                              = 365
  #     opt_in_to_archive_for_supported_resources = false
  #     cold_storage_after                        = 0
  #   }
  # }
}

resource "aws_backup_selection" "backup" {
  iam_role_arn = aws_iam_role.backup.arn
  name         = "s3"
  plan_id      = aws_backup_plan.backup.id

  resources    = ["arn:aws:s3:::${local.s3_prefix}-gvt-dsaid-${data.aws_caller_identity.current.account_id}-terraform-statefile"]

  # selection_tag {
  #   key   = "Project-Code"
  #   type  = "STRINGEQUALS"
  #   value = var.project_code
  # }
}

################################################################################
# iam
################################################################################
resource "aws_iam_role" "backup" {
  name               = "${local.role_name}backup"
  assume_role_policy = data.aws_iam_policy_document.backup-AssumeRole.json
  inline_policy {
    name   = "AllowPermissions"
    policy = data.aws_iam_policy_document.backup.json
  }
}

data "aws_iam_policy_document" "backup-AssumeRole" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["backup.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "backup" {
  statement {
    sid       = "ListAllMyBuckets"
    effect    = "Allow"
    resources = ["*"]
    actions   = ["s3:ListAllMyBuckets"]
  }

  statement {
    sid       = "AllowBucket"
    effect    = "Allow"
    resources = ["arn:aws:s3:::${local.s3_prefix}-${terraform.workspace}${var.zone}*-${var.project_code}-${data.aws_caller_identity.current.account_id}-*"]

    actions = [
      "s3:GetBucketTagging",
      "s3:GetInventoryConfiguration",
      "s3:ListBucketVersions",
      "s3:ListBucket",
      "s3:GetBucketVersioning",
      "s3:GetBucketLocation",
      "s3:GetBucketAcl",
      "s3:PutInventoryConfiguration",
      "s3:GetBucketNotification",
      "s3:PutBucketNotification",
    ]
  }

  statement {
    sid       = "AllowGetObject"
    effect    = "Allow"
    resources = ["arn:aws:s3:::${local.s3_prefix}-${terraform.workspace}${var.zone}*-${var.project_code}-${data.aws_caller_identity.current.account_id}-*/*"]

    actions = [
      "s3:GetObjectAcl",
      "s3:GetObject",
      "s3:GetObjectVersionTagging",
      "s3:GetObjectVersionAcl",
      "s3:GetObjectTagging",
      "s3:GetObjectVersion",
    ]
  }

  statement {
    sid       = "AllowTags"
    effect    = "Allow"
    resources = ["*"]
    actions   = ["tag:GetResources"]
  }

  statement {
    sid       = "AllowCloudwatch"
    effect    = "Allow"
    resources = ["*"]
    actions   = ["cloudwatch:GetMetricData"]
  }

  statement {
    sid       = "AllowEvents"
    effect    = "Allow"
    resources = ["arn:aws:events:*:*:rule/AwsBackupManagedRule*"]

    actions = [
      "events:DeleteRule",
      "events:PutTargets",
      "events:DescribeRule",
      "events:EnableRule",
      "events:PutRule",
      "events:RemoveTargets",
      "events:ListTargetsByRule",
      "events:DisableRule",
    ]
  }

  statement {
    sid       = "AllowEventsListAllRules"
    effect    = "Allow"
    resources = ["*"]
    actions   = ["events:ListRules"]
  }

  statement {
    sid       = "AllowKMS"
    effect    = "Allow"
    resources = ["arn:aws:kms:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:key/*"]

    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
    ]

    condition {
      test     = "StringLike"
      variable = "kms:ViaService"
      values   = ["s3.*.amazonaws.com"]
    }
  }
}