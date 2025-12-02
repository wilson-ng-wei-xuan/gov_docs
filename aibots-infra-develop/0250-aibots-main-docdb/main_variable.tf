variable "agency_code" {
  type = string
  default = "gvt"
}

variable "dept" {
  type  = string
  default = "dsaid"
}

variable "project_code" {
  type = string
  default = "aibots"
}

variable "project_desc" {
  type = string
  default = "main"
}

variable "zone" {
  type = string
  default = "ez"
}

variable "tier" {
  type = string
  default = "db"
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
}

variable "secret_rotation" {
  type = bool
  default = true
  description = <<EOT
    Each vpc comes with a default secret for the JWT hashing.
    Only VPC that has a public front end needs the JWT hashing to track user session.
    If set to true, you will need data.0004-sharedsvc-secret-rotation.tf
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_rotation
  EOT
}

variable "secret_rotation_schedule_expression" {
  type = string
  description = <<EOT
    The schedule to rotate secrets.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_rotation#schedule_expression
  EOT
}