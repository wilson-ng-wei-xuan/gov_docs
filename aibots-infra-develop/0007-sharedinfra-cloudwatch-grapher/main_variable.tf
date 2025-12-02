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
  default = "sharedinfra"
}

variable "project_desc" {
  type = string
  default = "cloudwatch-grapher"
}

variable "zone" {
  type = string
  default = "ez"
}

variable "tier" {
  type = string
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

variable "versioning" {
  type    = string
}

variable "force_destroy" {
  type    = bool
}

variable "bucket_key_enabled" {
  type    = bool
}