variable "agency_code" {
  type    = string
  default = "gvt"
}

variable "dept" {
  type    = string
  default = "gto"
}

variable "project_code" {
  type    = string
  default = "aibots"
}

variable "project_desc" {
  type    = string
  default = "rag-aoss-picker"
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
  type = string
}


# lambda
variable "retention_in_days" {
  type = number
}

variable "timeout" {
  type = number
}

## sqs
variable "delay_seconds" {
  type        = number
  default     = 0
  description = <<EOT
    (Optional) The time in seconds that the delivery of all messages in the queue will be delayed.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue
  EOT
}