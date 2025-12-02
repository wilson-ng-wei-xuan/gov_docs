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
  default = "sharedsvc"
}

variable "project_desc" {
  type    = string
  default = "s3bucket"
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
variable "buckets" {
  type    = list
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