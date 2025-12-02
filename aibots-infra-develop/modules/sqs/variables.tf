variable "name" {
  type        = string
  description = <<EOT
    (Required) The name of the resource, e.g. mysqs. This will be used in the name of the resources.
  EOT
}

##
## sqs policy specific variables
##
variable "account_id" {
  type        = string
  description = <<EOT
    (Required) The owner AWS account. This is to restrict access to dlq sqs only from within your account.
  EOT
}

# # this seems over engineering. remarked from >> resource "aws_sqs_queue_policy" "main"
variable "sqs_vpce_id" {
  type        = string
  default     = ""
  description = <<EOT
    (Required) The ID of the sqs VPC endpoint. This is to restrict sending sqs only from the endpoint in your sqs VPC endpoint.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint
  EOT
}

##
## sqs specific variables
##
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

variable "visibility_timeout_seconds" {
  type        = number
  default     = 30
  description = <<EOT
    (Optional) The visibility timeout for the queue.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue
  EOT
}

variable "redrive_policy_maxReceiveCount" {
  type        = number
  default     = 2
  description = <<EOT
    (Optional) The maxReceiveCount is the number of times a consumer tries receiving a message from a queue without deleting it before being moved to the dead-letter queue.
    Refer to: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html
  EOT
}