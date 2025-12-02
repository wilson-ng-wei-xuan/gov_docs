locals {
  # if length > 512, then truncate to 512; Ensure local.names do not throw an error
  function_name = substr( "${local.lambda_name}-${var.function_name}", 0, 64)
}
################################################################################
resource "aws_lambda_function" "simple_lambda" {
  count = var.ignore_changes ? 0 : 1 # use this if ignore_changes is false

  #checkov:skip=CKV_AWS_50: "X-ray tracing is enabled for Lambda"
  #checkov:skip=CKV_AWS_115: "Ensure that AWS Lambda function is configured for function-level concurrent execution limit"
  #checkov:skip=CKV_AWS_116: "Ensure that AWS Lambda function is configured for a Dead Letter Queue(DLQ)"
  #checkov:skip=CKV_AWS_173: "Check encryption settings for Lambda environmental variable"
  #checkov:skip=CKV_AWS_272: "Ensure AWS Lambda function is configured to validate code-signing"

  # # terraform does not allow passing ignore_changes as variable.
  # # simple_lambda_ignore_changes is created to ignore_changes
  # lifecycle {
  #   ignore_changes = [
  #     source_code_hash,
  #   ]
  # }

  function_name     = "${local.function_name}"

  package_type      = var.filename  != null ? "Zip" : "Image"
  filename          = var.filename  != null ? var.filename : null
  source_code_hash  = var.filename  != null ? filebase64sha256("${var.filename}") : null
  image_uri         = var.image_uri != null ? var.image_uri : null

  role              = aws_iam_role.lambda_role.arn
  handler           = "${var.handler}"
  runtime           = "${var.runtime}"
  
  memory_size       = "${var.memory_size}"
  timeout           = "${var.timeout}"
  
  environment {
    variables = "${var.environment_variables}"
  }
  
  layers = var.filename  != null ? "${var.layers}" : null

  vpc_config {
    security_group_ids = var.security_group_ids
    subnet_ids         = var.subnet_ids
  }

  tags = merge(
    { "Name" = "${local.function_name}" },
    local.tags,
    var.additional_tags
  )
}

################################################################################
# # terraform does not allow passing ignore_changes as variable.
# # simple_lambda_ignore_changes is created to ignore_changes
################################################################################
resource "aws_lambda_function" "simple_lambda_ignore_changes" {
  count = var.ignore_changes ? 1 : 0 # use this if ignore_changes is true

  #checkov:skip=CKV_AWS_50: "X-ray tracing is enabled for Lambda"
  #checkov:skip=CKV_AWS_115: "Ensure that AWS Lambda function is configured for function-level concurrent execution limit"
  #checkov:skip=CKV_AWS_116: "Ensure that AWS Lambda function is configured for a Dead Letter Queue(DLQ)"
  #checkov:skip=CKV_AWS_173: "Check encryption settings for Lambda environmental variable"
  #checkov:skip=CKV_AWS_272: "Ensure AWS Lambda function is configured to validate code-signing"

  # # terraform only handles infra, the application code is provided by CICD.
  # # we will ignore application code related changes.
  # # ignore_changes can only be a static list, so we cannot pass in variables.
  lifecycle {
    ignore_changes = [
      source_code_hash,
      # handler,
      # runtime,
      # memory_size,
      # timeout,
      # environment,
      # layers
    ]
  }

  function_name     = "${local.function_name}"

  package_type      = var.filename  != null ? "Zip" : "Image"
  filename          = var.filename  != null ? var.filename : null
  source_code_hash  = var.filename  != null ? filebase64sha256("${var.filename}") : null
  image_uri         = var.image_uri != null ? var.image_uri : null

  role              = aws_iam_role.lambda_role.arn
  handler           = "${var.handler}"
  runtime           = "${var.runtime}"
  
  memory_size       = "${var.memory_size}"
  timeout           = "${var.timeout}"
  
  environment {
    variables = "${var.environment_variables}"
  }
  
  layers = var.filename  != null ? "${var.layers}" : null

  vpc_config {
    security_group_ids = var.security_group_ids
    subnet_ids         = var.subnet_ids
  }

  tags = merge(
    { "Name" = "${local.function_name}" },
    local.tags,
    var.additional_tags
  )
}

################################################################################
locals {
  # if length > 512, then truncate to 512; Ensure local.names do not throw an error
  cw_name = substr( "/aws/lambda/${local.function_name}", 0, 512)
}

module "cloudwatch_log_group" {
  # source = "sgts.gitlab-dedicated.com/wog/svc-iac-layer-1-simple-s3-private-bucket/aws"
  # version = "~>2.0"
  source  = "../cloudwatch_log_group"
  # count   = var.access_logs == null ? 1 : 0 # create S3 bucket only if access logs are not provided

  name  = "${local.cw_name}"
  retention_in_days	= "${var.retention_in_days}"
  destination_arn = "${var.destination_arn}"
  filter_pattern = "${var.filter_pattern}"

  tags = var.tags
  additional_tags = merge(
    { "Name" = "${local.cw_name}" },
    var.additional_tags
  )
}

################################################################################

locals {
  # if length > 64, then truncate to 64; Ensure local.names do not throw an error
  lambda_role_name = substr( "${local.role_name}-${var.function_name}", 0, 64)
}

resource "aws_iam_role" "lambda_role" {
  name                = "${local.lambda_role_name}"
  description         = "Lambda role for ${var.function_name}"
  
  assume_role_policy  = jsonencode(
    {
      Version   = "2012-10-17"
      Statement = [
        {
          Action    = "sts:AssumeRole"
          Effect    = "Allow"
          Principal = {
            Service = "lambda.amazonaws.com"
          }
        },
      ]
    }
  )

  managed_policy_arns = "${var.managed_policy_arns}"

  dynamic "inline_policy" {
    for_each = var.inline_policy
    
    content {
      name     = inline_policy.value.name
      policy = inline_policy.value.policy
    }
  }

  permissions_boundary  = "${var.permissions_boundary}"

  tags = merge(
    { "Name" = "${local.lambda_role_name}" },
    local.tags,
    var.additional_tags
  )
}