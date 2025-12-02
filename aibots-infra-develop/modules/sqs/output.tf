output "sqs_queue_dlq" {
  value = aws_sqs_queue.dlq
  description = <<-EOT
    The secondary SQS acting as dead letter queue.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue
  EOT
}

output "sqs_queue_policy_dlq" {
  value = aws_sqs_queue_policy.dlq
  description = <<-EOT
    The queue policy of the secondary SQS.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue_policy
  EOT
}

output "sqs_queue"{
  value = aws_sqs_queue.main
  description = <<-EOT
    The primary SQS.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue
  EOT
}

output "sqs_queue_policy"{
  value = aws_sqs_queue_policy.main
  description = <<-EOT
    The queue policy of the primary SQS.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sqs_queue_policy
  EOT
}
