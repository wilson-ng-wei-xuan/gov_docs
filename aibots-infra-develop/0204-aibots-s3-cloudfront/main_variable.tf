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
  default = "cloudfront"
}

variable "zone" {
  type    = string
  default = "ez"
}

variable "tier" {
  type    = string
  default = "ingress"
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

variable "domain" {
  type    = string
  default = "aibots.gov.sg"
}

# you need to create the acm in NV for this cloudfront to recognise
variable "acm_certificate_arn" {
  type    = string
}

variable "secret_rotation" {
  type = bool
  default = true
}

variable "origin_path" {
  type = string
  default = ""
}

# s3
variable "versioning" {
  type = string
  default = "Enabled"
}

variable "force_destroy" {
  type = bool
  default = true
}

variable "bucket_key_enabled" {
  type = bool
  default = true
}

variable "secret_rotation_schedule_expression" {
  type = string
  description = <<EOT
    The schedule to rotate secrets.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_rotation#schedule_expression
  EOT
}