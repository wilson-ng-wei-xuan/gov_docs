resource "aws_iam_group" "read-only-group" {
  name = "read-only-group"
}

locals {
  read-only-group_policy_attachment = [
    "arn:aws:iam::aws:policy/job-function/ViewOnlyAccess",
    "arn:aws:iam::aws:policy/ReadOnlyAccess",
  ]
}

resource "aws_iam_group_policy_attachment" "read-only-group" {
  for_each = toset(local.read-only-group_policy_attachment)

  group      = aws_iam_group.read-only-group.name
  policy_arn = each.value
}

################################################################################
# CSG
################################################################################
resource "aws_iam_user" "csg-readonly-user" {
  name = "csg-readonly-user"
  path = "/"
  force_destroy = true

  tags = merge(
    { "Name" = "csg-readonly-user" },
    local.tags
  )
}

resource "aws_iam_user_group_membership" "csg-only-group" {
  user = aws_iam_user.csg-readonly-user.name

  groups = [
    aws_iam_group.read-only-group.name,
  ]
}

resource "aws_iam_user_policy_attachment" "csg-readonly-user" {
  user       = aws_iam_user.csg-readonly-user.name
  policy_arn = "arn:aws:iam::aws:policy/SecurityAudit"
}

################################################################################
# CASCOM
################################################################################
resource "aws_iam_user" "cascom-readonly-user" {
  name = "cascom-readonly-user"
  path = "/"
  force_destroy = true

  tags = merge(
    { "Name" = "cascom-readonly-user" },
    local.tags
  )
}

resource "aws_iam_access_key" "cascom-readonly-user" {
  lifecycle {
    ignore_changes = all
  }
  user = aws_iam_user.cascom-readonly-user.name
}

resource "aws_iam_user_group_membership" "cascom-only-group" {
  user = aws_iam_user.cascom-readonly-user.name

  groups = [
    aws_iam_group.read-only-group.name,
  ]
}

resource "aws_iam_policy" "cascom-readonly-user" {
  name        = "${local.policy_name}cascom-readonly-user"
  description = "Policy for cascom-readonly-user"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid = "AllowCostExplorerQueries"
        Effect   = "Allow"
        Action = [
          "ce:GetUsageForecast",
          "ce:GetTags",
          "ce:GetSavingsPlansUtilizationDetails",
          "ce:GetSavingsPlansUtilization",
          "ce:GetSavingsPlansPurchaseRecommendation",
          "ce:GetSavingsPlansCoverage",
          "ce:GetRightsizingRecommendation",
          "ce:GetReservationUtilization",
          "ce:GetReservationPurchaseRecommendation",
          "ce:GetReservationCoverage",
          "ce:GetPreferences",
          "ce:GetDimensionValues",
          "ce:GetCostForecast",
          "ce:GetCostAndUsageWithResources",
          "ce:GetCostAndUsage",
          "ce:GetAnomalySubscriptions",
          "ce:GetAnomalyMonitors",
          "ce:GetAnomalies",
          "ce:DescribeReport",
          "ce:DescribeNotificationSubscription",
          "ce:DescribeCostCategoryDefinition"
        ]
        Resource = "*"
      },
      {
        Sid = "AllowTrustedAdvisorQueries"
        Effect   = "Allow"
        Action = [
          "support:Describe*"
        ]
        Resource = "*"
      },

    ]
  })
}

resource "aws_iam_user_policy_attachment" "cascom-readonly-user" {
  user       = aws_iam_user.cascom-readonly-user.name
  policy_arn = aws_iam_policy.cascom-readonly-user.arn
}