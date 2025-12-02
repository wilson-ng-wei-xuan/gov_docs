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
  default = "api-redis"
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
variable "snapshot_retention_limit" {
  type = number
}