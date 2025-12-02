# this resource does not have a data
# we will pass it as local.cognito_user_pool_domain_wog-aad
resource "aws_cognito_user_pool_domain" "wog-aad" {
  domain       = "${terraform.workspace}-sso-${var.dept}"
  user_pool_id = aws_cognito_user_pool.wog-aad.id
}

resource "aws_cognito_user_pool" "wog-aad" {
  name = local.cognito_name

  alias_attributes         = ["email", ]
  auto_verified_attributes = ["email", ]

  deletion_protection = "INACTIVE"

  tags = merge(
    local.tags,
    {
      "Name" = local.cognito_name
    }
  )

  account_recovery_setting {
    recovery_mechanism {
      name     = "admin_only"
      priority = 1
    }
  }

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  username_configuration {
    case_sensitive = false
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
  }

  schema {
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    name                     = "email"
    required                 = true

    string_attribute_constraints {
      max_length = "2048"
      min_length = "0"
    }
  }
  schema {
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    name                     = "name"
    required                 = true

    string_attribute_constraints {
      max_length = "2048"
      min_length = "0"
    }
  }
  schema {
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    name                     = "preferred_username"
    required                 = true

    string_attribute_constraints {
      max_length = "2048"
      min_length = "0"
    }
  }
  schema {
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    name                     = "profile"
    required                 = true

    string_attribute_constraints {
      max_length = "2048"
      min_length = "0"
    }
  }
}

resource "aws_cognito_identity_provider" "wog-aad" {
  # https://login.microsoftonline.com/0b11c524-9a1c-4e1b-84cb-6336aefc2243/v2.0/.well-known/openid-configuration
  user_pool_id = aws_cognito_user_pool.wog-aad.id

  provider_name = aws_cognito_user_pool.wog-aad.name
  provider_type = "OIDC"
  provider_details = {
    "attributes_request_method"     = "POST"
    "attributes_url_add_attributes" = "false"
    "authorize_scopes"              = "openid profile email offline_access"
    "client_id"                     = jsondecode(data.aws_ssm_parameter.secret.value)["wog_oidc_client_id"]
    "client_secret"                 = jsondecode(data.aws_ssm_parameter.secret.value)["wog_oidc_client_secret"]
    "oidc_issuer"                   = "https://login.microsoftonline.com/0b11c524-9a1c-4e1b-84cb-6336aefc2243/v2.0"
    # below are input provided by me
    "authorize_url"  = "https://login.microsoftonline.com/0b11c524-9a1c-4e1b-84cb-6336aefc2243/oauth2/v2.0/authorize"
    "attributes_url" = "https://graph.microsoft.com/oidc/userinfo"
    "jwks_uri"       = "https://login.microsoftonline.com/0b11c524-9a1c-4e1b-84cb-6336aefc2243/discovery/v2.0/keys"
    "token_url"      = "https://login.microsoftonline.com/0b11c524-9a1c-4e1b-84cb-6336aefc2243/oauth2/v2.0/token"
  }

  attribute_mapping = {
    "email"              = "email"
    "email_verified"     = "email_verified"
    "name"               = "name"
    "preferred_username" = "preferred_username"
    "profile"            = "email"
    "username"           = "sub"
  }
}

data "aws_ssm_parameter" "secret" {
  depends_on = [aws_ssm_parameter.secret]

  name = aws_ssm_parameter.secret.name
}

resource "aws_ssm_parameter" "secret" {
  lifecycle {
    ignore_changes = [
      value,
    ]
  }

  name        = local.para_store_name
  description = "The Client ID and Secret provided to us during onboarding."
  type        = "SecureString"
  value       = jsonencode(var.key_pair)

  tags = merge(
    local.tags,
    {
      "Name" = local.para_store_name
    }
  )
}

variable "key_pair" {
  default = {
    wog_oidc_client_id     = "DEFAULT"
    wog_oidc_client_secret = "DEFAULT"
  }
  type = map(string)
}
