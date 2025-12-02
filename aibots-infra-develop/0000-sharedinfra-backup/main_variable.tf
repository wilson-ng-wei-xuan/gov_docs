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
  default = "backup"
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
