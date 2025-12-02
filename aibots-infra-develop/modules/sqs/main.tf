locals {
  # if length > 80, then truncate to 80; Ensure local.names do not throw an error
  # reduce by 4 chars to accomodate "-dlq"
  queue_name = substr( "${local.sqs_name}-${var.name}", 0, 76)
}

resource "aws_sqs_queue" "dlq" {
  name                        = "${local.queue_name}-dlq"
  delay_seconds               = var.delay_seconds
  max_message_size            = var.max_message_size
  message_retention_seconds   = var.message_retention_seconds
  receive_wait_time_seconds   = var.receive_wait_time_seconds
  sqs_managed_sse_enabled = true

  tags = merge(
  {
    "Name" = "${local.queue_name}-dlq" },
    local.tags,
    var.additional_tags
  )
}

resource "aws_sqs_queue_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id

  policy = <<POLICY
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "owner",
        "Effect": "Allow",
        "Principal": {
          "AWS": [ "${var.account_id}" ]
        },
        "Action": "sqs:*",
        "Resource": "${aws_sqs_queue.dlq.arn}"
      }
    ]
  }
  POLICY
}

resource "aws_sqs_queue" "main" {
  name                        = "${local.queue_name}"
  delay_seconds               = var.delay_seconds
  max_message_size            = var.max_message_size
  message_retention_seconds   = var.message_retention_seconds
  receive_wait_time_seconds   = var.receive_wait_time_seconds
  visibility_timeout_seconds  = var.visibility_timeout_seconds
  sqs_managed_sse_enabled = true

  redrive_policy              = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.redrive_policy_maxReceiveCount
  })

  tags = merge(
  {
    "Name" = "${local.queue_name}" },
    local.tags,
    var.additional_tags
  )
}

resource "aws_sqs_queue_policy" "main" {
  queue_url = aws_sqs_queue.main.id

  policy = <<POLICY
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "owner",
        "Effect": "Allow",
        "Principal": {
          "AWS": [ "${var.account_id}" ]
        },
        "Action": "sqs:*",
        "Resource": "${aws_sqs_queue.main.arn}"
      }
    ]
  }
  POLICY
}
        # "Condition": {
        #   "StringNotEquals": {
        #     "aws:sourceVpce": "${var.sqs_vpce_id}"
        #   }
        # },