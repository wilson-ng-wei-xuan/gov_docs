# This is for Security Hub findings:
# [IAM.18] Ensure a support role has been created to manage incidents with AWS Support
# refer to https://docs.aws.amazon.com/securityhub/latest/userguide/iam-controls.html#iam-18
resource "aws_iam_role" "aws-support-access" {
  name        = "${local.role_name}aws-support-access"
  description = "Security Hub findings requirement, IAM.18 - Ensure a support role has been created to manage incidents with AWS Support"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        "Sid" : "",
        "Effect" : "Allow",
        "Principal" : {
          "AWS" : "arn:aws:iam::058264159304:root"
        },
        "Action" : "sts:AssumeRole",
        "Condition" : {}
      },
    ]
  })

  tags = merge(
    { "Name" = "${local.role_name}aws-support-access" },
    local.tags
  )
}

resource "aws_iam_role_policy_attachment" "aws-support-access" {
  role       = aws_iam_role.aws-support-access.name
  policy_arn = "arn:aws:iam::aws:policy/AWSSupportAccess"
}