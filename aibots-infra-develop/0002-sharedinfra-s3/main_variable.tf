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
# s3
variable "buckets" {
  type = list
  default = ["athena", "cost-usage-reports", "access-logs-elb", "access-logs-cloudfront"]
}

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