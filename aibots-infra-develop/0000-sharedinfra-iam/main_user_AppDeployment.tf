resource "aws_iam_user" "AppDeployment" {
  name  = "iam-user-AppDeployment"
  path  = "/"

  tags = merge(
    { "Name" = "iam-user-AppDeployment" },
    local.tags
  )
}

resource "aws_iam_user_policy" "AppDeployment" {
  depends_on = [ aws_iam_user.AppDeployment ]

  user   = "iam-user-AppDeployment"
  name   = "iam-policy-AppDeployment"
  policy = data.aws_iam_policy_document.AppDeployment.json
}

data "aws_iam_policy_document" "AppDeployment" {
  statement {
    sid       = "AppDeployment"
    effect    = "Allow"
    actions   = [
      "ecr:*",
      "lambda:*"
    ]
    resources = ["*"]
  }
}