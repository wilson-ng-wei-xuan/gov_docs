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
  default = "sharedsvc"
}

variable "project_desc" {
  type    = string
  default = "scheduler"
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
# scheduler
variable "schedule" {
  type = list(any)
}

# lambda
variable "retention_in_days" {
  type = number
}

variable "timeout" {
  type = number
}