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
  default = "aibots"
}

variable "project_desc" {
  type    = string
  default = "rag-parse"
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
# lambda
variable "process" {
  type = list(any)
  # name          - (Required) Suffix of the name. To differentiate the deployment.
  # package_type  - (Optional) Lambda deployment package type. Valid values are Zip and Image. Defaults to Zip.
  default = [
    {
      name = "zip"
      package_type = "Zip"
    },
    {
      name = "docx"
      package_type = "Image"
    },
    {
      name = "xlsx"
      package_type = "Image"
    },
    {
      name = "pptx"
      package_type = "Image"
    },
    {
      name = "csv"
      package_type = "Image"
    },
    {
      name = "txt"
      package_type = "Image"
    },
    {
      name = "pdf"
      package_type = "Image"
    }
  ]
}

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

variable "max_message_size" {
  type        = number
  default     = 262144
  description = <<EOT
    (Optional) The limit of how many bytes a message can contain before Amazon SQS rejects it.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue
  EOT
}

variable "message_retention_seconds" {
  type        = number
  default     = 345600
  description = <<EOT
    (Optional) The number of seconds Amazon SQS retains a message.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue
  EOT
}

variable "receive_wait_time_seconds" {
  type        = number
  default     = 0
  description = <<EOT
    (Optional) The time for which a ReceiveMessage call will wait for a message to arrive (long polling) before returning.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue
  EOT
}

# https://docs.aws.amazon.com/lambda/latest/operatorguide/sqs-retries.html
# In an application under heavy load or with spiky traffic patterns, it’s recommended that you:

# Set the maxReceiveCount on the source queue’s redrive policy to at least 5.
# This improves the chances of messages being processed before reaching the DLQ.
variable "redrive_policy_maxReceiveCount" {
  type        = number
  default     = 2
  description = <<EOT
    (Optional) The maxReceiveCount is the number of times a consumer tries receiving a message from a queue without deleting it before being moved to the dead-letter queue.
    Refer to: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html
  EOT
}