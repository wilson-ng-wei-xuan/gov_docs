resource "aws_shield_protection" "project" {
  name         = aws_cloudfront_distribution.project.comment
  resource_arn = aws_cloudfront_distribution.project.arn

  tags = merge(
    local.tags,
    { "Name"  = aws_cloudfront_distribution.project.comment }
  )
}