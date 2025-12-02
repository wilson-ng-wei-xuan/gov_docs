module "ses_user" {
  source = "../modules/smtp_user"

  name = "${var.project_desc}-${var.from}"
  from = var.from
  domain = "${local.route53_zone_prefix}${var.domain}"
  layers = [ data.aws_lambda_layer_version.LambdaInsightsExtension.id ]
  destination_arn = data.aws_lambda_function.notification.arn
  retention_in_days = 7
  secret_rotation_schedule_expression = var.secret_rotation_schedule_expression
  tags = local.tags
}