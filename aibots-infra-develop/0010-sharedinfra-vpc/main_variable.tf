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
  default = "sharedinfra"
}

variable "project_desc" {
  type    = string
  default = ""
}

variable "zone" {
  type    = string
  default = "ez"
}

variable "tier" {
  type    = string
  default = ""
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

variable "deploy_igw" {
  type = bool
}

variable "vpc_cidr_block" {
  type = string
}

variable "subnets" {
  type = list(any)
}

variable "secret_rotation" {
  type = bool
  default = false
  description = <<EOT
    Each vpc comes with a default secret for the JWT hashing.
    Only VPC that has a public front end needs the JWT hashing to track user session.
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