resource "aws_ses_domain_identity" "domain" {
  count  = length(var.domain)
  domain = var.domain[count.index]
}

resource "aws_ses_domain_dkim" "domain" {
  count  = length(var.domain)
  domain = aws_ses_domain_identity.domain[count.index].domain
}

resource "aws_ses_domain_mail_from" "domain" {
  count            = length(var.domain)
  domain           = aws_ses_domain_identity.domain[count.index].domain
  mail_from_domain = "mail.${aws_ses_domain_identity.domain[count.index].domain}"
}

# resource "aws_ses_domain_identity_verification" "domain" {
#   count = length( var.domain )
#   domain = var.domain[ count.index ]
# }
