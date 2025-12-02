resource "aws_account_alternate_contact" "billing" {
  alternate_contact_type = "BILLING"

  name          = "GovTech"
  title         = "dsaid"
  email_address = "data@tech.gov.sg"
  phone_number  = "+65"
}

resource "aws_account_alternate_contact" "operations" {
  alternate_contact_type = "OPERATIONS"

  name          = "GovTech"
  title         = "dsaid"
  email_address = "data@tech.gov.sg"
  phone_number  = "+65"
}

resource "aws_account_alternate_contact" "security" {
  alternate_contact_type = "SECURITY"

  name          = "GovTech"
  title         = "dsaid"
  email_address = "data@tech.gov.sg"
  phone_number  = "+65"
}