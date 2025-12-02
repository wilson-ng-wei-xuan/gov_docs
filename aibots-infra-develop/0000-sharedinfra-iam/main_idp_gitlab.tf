module "aws_idp_gitlab" {
  source  = "registry.terraform.io/terraform-module/gitlab-oidc-provider/aws"
  version = "~> 1"

  tags                 = local.tags
  create_oidc_provider = true
  create_oidc_role     = false
  url                  = "https://sgts.gitlab-dedicated.com"

  # in rare cases https://xyz:443 is different than tls://xyz:443
  # switch to custom module for this rare case
  # https://sgts.gitlab-dedicated.com/wog/gvt/gds-ace/general/infra/terraform-modules/-/tree/master/oidc-provider
  gitlab_tls_url            = "https://sgts.gitlab-dedicated.com:443"
  aud_value                 = ["https://sgts.gitlab-dedicated.com"]
  oidc_role_attach_policies = ["${aws_iam_role.gitlab.arn}"]
}
