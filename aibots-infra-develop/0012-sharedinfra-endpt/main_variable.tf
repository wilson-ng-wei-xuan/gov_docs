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
  default = ""
}

variable "zone" {
  type    = string
  default = "ez"
}

variable "tier" {
  type    = string
  default = "endpt"
}

variable "ops_enddate" {
  type    = string
  default = "dec 2099"
}

#######################################################
## project specific variables
## supply the value in ./environments/project.[env].tfvars
#######################################################
# variable "interface_endpts" {
#   type = list(any)
# }
variable "interface_endpts" {
  type        = list(
    object(
      {
        service_name        = string
        name                = optional(string)
        restrict_oubound    = optional(bool, true)
        private_dns_enabled = optional(bool, false)
      }
    )
  )
}