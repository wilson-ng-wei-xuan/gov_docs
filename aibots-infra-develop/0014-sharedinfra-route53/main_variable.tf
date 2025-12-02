variable "agency_code" {
  type    = string
  default = "gvt"
}

variable "dept" {
  type    = string
  default = "gdp"
}

variable "project_code" {
  type    = string
  default = "sharedinfra"
}

variable "project_desc" {
  type    = string
  default = "route53"
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
# you cannot based it on the domain name because the output file needs to use
# $${local.route53_zone_prefix} as part of the variable
variable "hosted_zone_name" {
  type    = string
  default = "aibots.gov.sg"
}

variable "record" {
  type    = string
  default = "internal"
}