# Mandatory Parameters --------------------------------------------------------
variable "name" {
  type        = string
  description = "The name of the LB. This name must be unique within your AWS account, can have a maximum of 32 characters, must contain only alphanumeric characters or hyphens, and must not begin or end with a hyphen. If not specified, Terraform will autogenerate a name beginning with"
  validation {
    condition     = length(var.name) <= 32
    error_message = "The name must be less than 32 characters."
  }
  validation {
    condition     = can(regex("^[a-zA-Z0-9-]+$", var.name))
    error_message = "The name must contain only alphanumeric characters or hyphens."
  }
}

variable "vpc_id" {
  type        = string
  description = "(Required) The VPC ID of the virtual private cloud in which the SFTP server's endpoint will be hosted."
}

variable "subnet_ids" {
  type        = list(string)
  description = "(Required) A list of subnet IDs that are required to host your SFTP server endpoint in your VPC."
}

variable "subnet_mapping" {
  type        = list(string)
  default     = []
  description = "(Optional) A list of eip.id for subnet mapping, Shield Advance requirement."
}

variable "access_logs" {
  type = object({
    bucket = string
    # prefix = string
  })
  description = <<-EOT
    (Optional) An access logs block. Supports the following properties below.
        bucket - (Required) The S3 bucket name to store the logs in.
        # prefix - (Optional) The S3 bucket prefix. Logs are stored in the root if not configured.
    Access Logs are always enabled.
    EOT
  default     = null
}

variable "aws_s3_bucket_logging" {
  type        = string
  description = <<EOT
    (Optional) But this is a IM requirement. CS 1.6/S4d, CS 1.3/S2c
    So you should already create this s3_bucket_logging somewhere and pass in the bucket.id
    "https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_logging"
  EOT
  default     = null
}

# Optional Parameters --------------------------------------------------------
variable "load_balancer_type" {
  type        = string
  description = "The type of load balancer to create. Possible values are application or network."
  default     = "application"
  validation {
    condition     = contains(["application", "network"], var.load_balancer_type)
    error_message = "Invalid input, options: \"application\", \"network\"."
  }
}

variable "enable_deletion_protection" {
  type        = bool
  description = "(Optional) Whether deletion protection is enabled. Defaults to false."
  default     = false
}

variable "force_destroy" {
  type        = bool
  description = <<EOF
    (Optional) A boolean that indicates all objects should be deleted from the bucket so that the bucket can be destroyed without error. These objects are not recoverable. Defaults to false.
    WARNING! NOT RECOMMENDED FOR PRODUCTION USE.
  EOF
  default     = false
}

variable "bucket_key_enabled" {
  type        = bool
  description = "https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-key.html"
  default     = true
}

variable "ip_address_type" {
  type        = string
  description = <<EOF
    (Optional)  (Optional, forces new resource) The type of IP addresses used by the target group, only supported when target type is set to ip. Possible values are ipv4 or ipv6.
  EOF
  default     = "ipv4"

  validation {
    condition     = can(regex("^(ipv4|ipv6)$", var.ip_address_type))
    error_message = "The ip_address_type must be either ipv4 or ipv6."
  }
}

variable "security_group_ids" {
  type        = list(string)
  description = "(Optional) A list of security groups IDs that are available to attach to your Application Load Balancer. If left blank, a new Security Group will be created."
  default     = null
}

variable "security_group_ingress_cidr_blocks" {
  type        = list(string)
  default     = ["0.0.0.0/0"]
  description = "List of CIDR blocks to allow access to Application Load Balancer. This would be the VPC CIDR block if not provided. **NOTE: This is only applicable if security_group_ids is not provided**"
}

variable "elb-account-id" {
  type        = string
  description = <<-EOT
    ELB account for the region. This is NOT your accountid. 
    e.g : Asia Pacific (Singapore) – 114774131450
    See https://docs.aws.amazon.com/elasticloadbalancing/latest/application/enable-access-logging.html
    Default value is 114774131450 (Singapore)
  EOT

  default = "114774131450"

}

variable "certificate_arn" {
  type        = list
  description = "(Optional) If available, a listener will be created accepting traffic at port 443."
  default     = null
}

variable "ssl_policy" {
  type        = string
  description = <<-EOT
    (Optional) SSL Policy for the 443 listener.
    See https://docs.aws.amazon.com/elasticloadbalancing/latest/application/create-https-listener.html
  EOT
  default     = "ELBSecurityPolicy-FS-1-2-Res-2020-10"
}

variable "internal" {
  type        = bool
  description = "(Optional) If true, the LB will be internal."
  default     = false
}

variable "versioning" {
  type        = string
  description = "(Optional) Configuration of the S3 bucket versioning state."
  default     = "Disabled"
}

variable "web_acl_arn" {
  type        = string
  description = "(Optional) If available, alb will be associated with the WAF."
  default     = null
}

variable "idle_timeout" {
  type        = string
  description = <<-EOT
    (Optional) The time in seconds that the connection is allowed to be idle. Only valid for Load Balancers of type application.
    See https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb#idle_timeout
  EOT
  default     = 60
}