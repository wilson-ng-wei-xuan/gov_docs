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
  default = "sharedsvc"
}

variable "project_desc" {
  type = string
  default = "api"
}

variable "zone" {
  type = string
  default = "ez"
}

variable "tier" {
  type = string
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
variable "pte_api" {
  type = list
}

variable "certificate_arn" {
  type = list
}

######################################################################################
# ALB listener and Target Group
######################################################################################
variable "lb_listener_rule_priority" {
  type = number
}