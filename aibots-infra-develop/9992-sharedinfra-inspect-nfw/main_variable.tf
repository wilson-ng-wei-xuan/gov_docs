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
  default = "sharedinfra"
}

variable "project_desc" {
  type = string
  default = ""
}

variable "zone" {
  type = string
  default = "ez"
}

variable "tier" {
  type = string
  default = "inspect"
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

variable "filter_pattern" {
  type        = string
  default     = "?\"[NOTIFY]\" ?\"[ERROR]\" ?\"[WARNING]\" ?\"[WARN]\" ?\"[CRITICAL]\" ?\"caught SIGTERM, shutting down\""
  description = <<EOT
    CloudWatch Logs filter pattern for subscribing to a filtered stream of log events.
    Since we are deploying lambda, we just default it to something that is more Lambda.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_subscription_filter#filter_pattern
  EOT
}

variable "govtech_llmstack_endpoint" {
  type        = string
  description = <<EOT
    the govtech_llmstack_endpoints that you want to call
    sit uat and prd has a different endpoint.
  EOT
}

variable "govtech_govtext_endpoint" {
  type        = string
  description = <<EOT
    the govtech_govtext_endpoints that you want to call
    sit uat and prd has a different endpoint.
  EOT
}