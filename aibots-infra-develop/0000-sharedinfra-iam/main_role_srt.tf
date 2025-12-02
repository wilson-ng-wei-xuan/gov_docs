# This is for Shield Advanced configuration
# https://docs.aws.amazon.com/waf/latest/DDOSAPIReference/API_AssociateDRTRole.html
resource "aws_iam_role" "srt" {
  name        = "${local.role_name}shield-response-team"
  description = "Allows AWS Shield Response Team."
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        "Sid" : "",
        "Effect" : "Allow",
        "Principal" : {
          "Service" : "drt.shield.amazonaws.com"
        },
        "Action" : "sts:AssumeRole"
      },
    ]
  })

  tags = merge(
    { "Name" = "${local.role_name}shield-response-team" },
    local.tags
  )
}

resource "aws_iam_role_policy_attachment" "srt" {
  role       = aws_iam_role.srt.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSShieldDRTAccessPolicy"
}

resource "aws_shield_drt_access_role_arn_association" "srt" {
  role_arn = aws_iam_role.srt.arn
}