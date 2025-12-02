variable "agency_code" {
  type    = string
  default = "gvt"
}

variable "dept" {
  type    = string
  default = "dsaid"
}

variable "project_code" {
  type    = string
  default = "aibots"
}

variable "project_desc" {
  type    = string
  default = "smtp-user"
}

variable "zone" {
  type    = string
  default = "ez"
}

variable "tier" {
  type    = string
  default = "app"
}

variable "ops_enddate" {
  type    = string
  default = "dec 2099"
}

#######################################################
## project specific variables
## supply the value in ./environments/project.[env].tfvars
#######################################################
variable "retention_in_days" {
  type = number
  description = <<EOT
    The number of days for cloudwatch logs retention_in_days
  EOT
}

variable "domain" {
  type    = string
  default = "aibots.gov.sg"
}

variable "from" {
  type    = string
  default = "no-reply"
}

variable "secret_rotation_schedule_expression" {
  type = string
  description = <<EOT
    The schedule to rotate secrets.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_rotation#schedule_expression
  EOT
}