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
  default = "rag"
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

variable "aoss_count" {
  type = number
  validation {
    condition     = var.aoss_count >= 0 && var.aoss_count <= 20
    error_message = "Accepted values: 1-20."
  }
}