resource "aws_iam_user_policy" "smtp_user" {
  name = "${local.policy_name}-${local.smtp_user_name}"
  user = aws_iam_user.smtp_user.name

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ses:SendRawEmail",
        ]
        Effect   = "Allow"
        Resource = "arn:aws:ses:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:identity/${var.domain}"
        Condition = {
          StringEquals = {
            "ses:FromAddress" = "${var.from}@${var.domain}"
          }
        }
      },
      {
        Action   = [
          "s3:PutObject",
        ]
        Effect   = "Allow"
        Resource = [
          "${data.aws_s3_bucket.email.arn}/${var.tags.Project-Code}/*",
        ]
      },
    ]
  })
}

resource "aws_iam_user" "smtp_user" {
  name = "${local.user_name}-${local.smtp_user_name}"

  tags = merge(     
    local.tags,
    var.additional_tags,
    { "Name" = "${local.user_name}-${local.smtp_user_name}" }
  )

}

resource "aws_iam_access_key" "smtp_user" {
  lifecycle {
    ignore_changes = all
  }
  user = aws_iam_user.smtp_user.name
}