variable "bucket" {
  type        = string
  description = "The name of the bucket."
  default     = "-"

  # only alphanumeric characters and dashes are allowed
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.bucket))
    error_message = "The bucket name can contain only lowercase alphanumeric characters and dashes."
  }
}

variable "force_destroy" {
  type        = bool
  description = "A boolean that indicates all objects should be deleted from the bucket so that the bucket can be destroyed without error. These objects are not recoverable. Defaults to false. Should only be true for testing purpose."
  default     = false
}

variable "versioning" {
  type        = string
  description = "The versioning state of the bucket. Valid values: Enabled, Suspended, or Disabled. Disabled should only be used when creating or importing resources that correspond to unversioned S3 buckets."
  default     = "Enabled"

  validation {
    condition     = can(regex("^(Enabled|Suspended|Disabled)$", var.versioning))
    error_message = "The versioning state of the bucket must be Enabled, Suspended, or Disabled."
  }
}

variable "bucket_policy" {
  type        = any
  description = "The s3 bucket policy."
  default     = null
}

variable "bucket_key_enabled" {
  type        = bool
  description = "https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-key.html"
  default     = true
}

variable "aws_s3_bucket_logging" {
  type        = string
  description = <<EOT
    (Optional) But this is a IM requirement. CS 1.6/S4d, CS 1.3/S2c
    "https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_logging"
  EOT
  default     = null
}

variable "keep_default_lifecycle" {
  type        = bool
  description = <<EOT
    Keep the default lifecycle configuration.
    default cleanup deleted files : with versioning enabled, this lifecycle deletes all noncurrent versions.
  EOT
  default     = true
}

variable "additional_lifecycle" {
  type        = list
  description = <<EOT
    Additional lifecycle configuration. e.g.:
      additional_lifecycle = [ {
        id = "cleanup archive files"
        status = "Enabled"
        filter = {
          prefix = "batch/archive"
        }
        noncurrent_version_expiration = {
          noncurrent_days = 7
          newer_noncurrent_versions = null
        }
        abort_incomplete_multipart_upload = {
          days_after_initiation = 1
        }
        expiration = {
          expired_object_delete_marker = true
        }
      } ]
  EOT
  default     = []
}


variable "noncurrent_days" {
  type        = number
  description = <<EOT
    Number of days an object is noncurrent before noncurrent_version_expiration.
    "https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_lifecycle_configuration#noncurrent_version_expiration"
    Only effective if keep_default_lifecycle = true
  EOT
  default     = 7
}

variable "newer_noncurrent_versions" {
  type        = number
  description = <<EOT
    Number of noncurrent versions Amazon S3 will retain.
    "https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_lifecycle_configuration#noncurrent_version_expiration"
    Only effective if keep_default_lifecycle = true
  EOT
  default     = null
}

