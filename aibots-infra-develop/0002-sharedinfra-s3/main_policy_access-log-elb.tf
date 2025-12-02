data "aws_iam_policy_document" "access-logs-elb" {
  # https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-access-logs.html#access-logging-bucket-requirements
  # Allow AWS account to put files
  statement {
    sid = "albAWSLogDeliveryWrite"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::114774131450:root"] # this is AWS elb logs delivery account_id
    }
    actions = [
      "s3:PutObject"
    ]
    resources = [
      "arn:aws:s3:::${local.s3_prefix}-${terraform.workspace}${var.zone}-${var.project_code}-${data.aws_caller_identity.current.account_id}-access-logs-elb/*"
    ]
  }

  statement {
    sid = "nlbAWSLogDeliveryAclCheck"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }
    actions = [
      "s3:GetBucketAcl"
    ]
    resources = [
      "arn:aws:s3:::${local.s3_prefix}-${terraform.workspace}${var.zone}-${var.project_code}-${data.aws_caller_identity.current.account_id}-access-logs-elb"
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values = [
        "${data.aws_caller_identity.current.account_id}",
      ]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values = [
        "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*",
      ]
    }
  }

  statement {
    sid = "nlbAWSLogDeliveryWrite"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }
    actions = [
      "s3:PutObject"
    ]
    resources = [
      "arn:aws:s3:::${local.s3_prefix}-${terraform.workspace}${var.zone}-${var.project_code}-${data.aws_caller_identity.current.account_id}-access-logs-elb/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values = [
        "${data.aws_caller_identity.current.account_id}",
      ]
    }

    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values = [
        "bucket-owner-full-control",
      ]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values = [
        "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*",
      ]
    }
  }
}