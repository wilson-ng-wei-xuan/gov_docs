resource "aws_cognito_user_pool_client" "client" {
  count         = var.cognito_user_pool_domain == null ? 0 : 1
  user_pool_id = var.aws_cognito_user_pools.ids[0]
  name    = var.host_header[0]

  supported_identity_providers  = [ var.aws_cognito_user_pools.id ]

  callback_urls = [
    "https://${var.host_header[0]}",
    "https://${var.host_header[0]}/oauth2/idpresponse",
  ]

  generate_secret     = true

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "minutes"
  }
  auth_session_validity                         = 3
  access_token_validity                         = 60
  id_token_validity                             = 60
  refresh_token_validity                        = 480

  allowed_oauth_flows                           = [
    "code",
  ]
  allowed_oauth_flows_user_pool_client          = true
  allowed_oauth_scopes                          = [
    "email",
    "openid",
    "profile",
  ]

  enable_propagate_additional_user_context_data = false
  enable_token_revocation                       = true
  prevent_user_existence_errors                 = "ENABLED"
  explicit_auth_flows                           = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH",
  ]
}

# ######################################################################################
# # ALB listener and Target Group
# ######################################################################################
# resource "aws_lb_target_group" "lb_target_group" {
#   name = "${local.alb_tg_name}"

#   tags = merge(
#     local.tags,
#     {
#       "Name" = local.alb_tg_name,
#     }
#   )

#   target_type = "lambda"
# }

# locals {
#   priority = split("-", local.path)[0]
# }

# resource "aws_lb_listener_rule" "lb_listener_rule" {
#   # lifecycle {
#   #   ignore_changes = [
#   #     priority,
#   #   ]
#   # }
  
#   listener_arn = data.aws_lb_listener.ezdmzalb_pte_443.arn
#   priority   = var.lb_listener_rule_priority + local.priority

#   tags = merge(
#     local.tags,
#     {
#       "Name" = local.alb_lsnr_rule_name,
#     }
#   )

#   action {
#     type = "authenticate-cognito"

#     authenticate_cognito {
#       user_pool_arn       = data.aws_cognito_user_pools.wog-aad.arns[0]
#       user_pool_client_id = aws_cognito_user_pool_client.client.id
#       user_pool_domain    = local.cognito_user_pool_domain_wog-aad
#       session_timeout     = 28800
#     }
#   }

#   # action {
#   #   type = "authenticate-oidc"

#   #   authenticate_oidc {
#   #     client_id               = aws_cognito_user_pool_client.client.id
#   #     client_secret           = aws_cognito_user_pool_client.client.client_secret
#   #     issuer                  = "https://cognito-idp.${data.aws_region.current.name}.amazonaws.com/${tolist(data.aws_cognito_user_pools.wog-aad.ids)[0]}"
#   #     authorization_endpoint  = "https://${local.cognito_domain_wog-aad}.auth.${data.aws_region.current.name}.amazoncognito.com/oauth2/authorize"
#   #     token_endpoint          = "https://${local.cognito_domain_wog-aad}.auth.${data.aws_region.current.name}.amazoncognito.com/oauth2/token"
#   #     user_info_endpoint      = "https://${local.cognito_domain_wog-aad}.auth.${data.aws_region.current.name}.amazoncognito.com/oauth2/userInfo"
#   #     session_timeout         = 28800
#   #   }
#   # }
#   condition {
#     host_header {
#       values = var.lb_listener_rule_host_header
#     }
#   }

#   action {
#     target_group_arn = aws_lb_target_group.lb_target_group.arn
#     type             = "forward"
#   }
#   condition {
#     host_header {
#       values = var.lb_listener_rule_host_header
#     }
#   }
# }

# resource "aws_lb_listener_certificate" "lb_listener_cert" {
#   count = var.certificate_arn == null ? 0 : 1

#   listener_arn    = data.aws_lb_listener.ezdmzalb_pte_443.arn
#   certificate_arn = var.certificate_arn
# }

# ######################################################################################
# # give lambda the permission
# ######################################################################################
# resource "aws_lambda_permission" "AllowExecutionFromlb" {
#   statement_id  = "AllowExecutionFromlb"
#   action        = "lambda:InvokeFunction"
#   function_name = module.simple_lambda.lambda_function.arn
#   principal     = "elasticloadbalancing.amazonaws.com"
#   source_arn    = aws_lb_target_group.lb_target_group.arn
# }

# ######################################################################################
# # attach the lambda to the target group
# ######################################################################################
# resource "aws_lb_target_group_attachment" "lb_target_group_attachment" {
#   target_group_arn = aws_lb_target_group.lb_target_group.arn
#   target_id    = module.simple_lambda.lambda_function.arn
#   depends_on   = [aws_lambda_permission.AllowExecutionFromlb]
# }