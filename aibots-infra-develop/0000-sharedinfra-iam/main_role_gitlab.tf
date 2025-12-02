resource "aws_iam_role" "gitlab" {
  name        = "${local.role_name}gitlab"
  description = "Allows Gitlab to connect."

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/ReadOnlyAccess"
  ]

  assume_role_policy = jsonencode(
    {
      Statement = [
        {
          "Effect": "Allow",
          "Principal": {
            "Federated": "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/sgts.gitlab-dedicated.com"
          },
          "Action": "sts:AssumeRoleWithWebIdentity",
          "Condition": {
            "StringEquals": {
              "sgts.gitlab-dedicated.com:aud": ["https://sgts.gitlab-dedicated.com"]
            }
            "StringLike": {
              "sgts.gitlab-dedicated.com:sub": [
                "project_path:wog/gvt/dsaid-st/moonshot/aibots/*",
              ]
            }
          }
        }
      ]
      Version = "2012-10-17"
    }
  )

  inline_policy {
    name   = "GitLabPolicy"
    policy = data.aws_iam_policy_document.gitlab.json
  }

  tags = merge(
    { "Name" = "${local.role_name}gitlab" },
    local.tags
  )
}

data "aws_iam_policy_document" "gitlab" {
  statement {
    sid = "AllowECRPush"
    effect = "Allow"
    actions = [
      "ecr:CompleteLayerUpload",
      "ecr:GetAuthorizationToken",
      "ecr:UploadLayerPart",
      "ecr:InitiateLayerUpload",
      "ecr:BatchCheckLayerAvailability",
      "ecr:PutImage"
    ]
    resources = ["*"]
  }
  statement {
    sid = "AllowAssumeRole"
    effect = "Allow"
    actions = [
      "sts:AssumeRole",
      "sts:SetSourceIdentity"
    ]
    resources = ["*"]
  }
}