locals {
  # if length > 512, then truncate to 512; Ensure local.names do not throw an error

  # rotator are unique, as they are deployed out of VPC.
  # thus we need to
  # 1. manually craft out and remove the ${local.tags.Zone} from the function_name
  #    function_name = substr( "${local.lambda_name}-${local.tags.Project-Code}-secret-rotator-db", 0, 64)
  # 2. hardcode the ecs:StopTask permission to app cos fargate are deployed in app tire
  #    ${local.ecs_cluster_prefix}-${terraform.workspace}${local.tags.Zone}app-${local.tags.Project-Code}-*
  function_name = substr( "${local.lambda_prefix}-${local.tags.Environment}${local.tags.Zone}-${local.tags.Project-Code}-secret-rotator-db", 0, 64)
}

resource "aws_lambda_function" "simple_lambda" {
  #checkov:skip=CKV_AWS_50: "X-ray tracing is enabled for Lambda"
  #checkov:skip=CKV_AWS_115: "Ensure that AWS Lambda function is configured for function-level concurrent execution limit"
  #checkov:skip=CKV_AWS_116: "Ensure that AWS Lambda function is configured for a Dead Letter Queue(DLQ)"
  #checkov:skip=CKV_AWS_173: "Check encryption settings for Lambda environmental variable"
  #checkov:skip=CKV_AWS_272: "Ensure AWS Lambda function is configured to validate code-signing"

  # terraform only handles infra, the application code is provided by CICD.
  # we will ignore application code related changes.
  # ignore_changes can only be a static list, so we cannot pass in variables.
  # lifecycle {
  #   ignore_changes = [
  #     source_code_hash,
  #     handler,
  #     runtime,
  #     memory_size,
  #     timeout,
  #     environment,
  #     layers
  #   ]
  # }

  function_name     = "${local.function_name}"
  
  filename          = "${path.module}/source/lambda/project.zip"
  source_code_hash  = filebase64sha256( "${path.module}/source/lambda/project.zip" )
  
  role              = aws_iam_role.lambda_role.arn
  handler           = "lambda_function.lambda_handler" # "${var.handler}"
  runtime           = "python3.12" # "${var.runtime}"
  
  memory_size       = 128 # "${var.memory_size}"
  timeout           = 10 # "${var.timeout}"
  
  environment {
    variables = { "DB_CLUSTER_IDENTIFIER": var.dbclusteridentifier }
  }
  
  layers = "${var.layers}"
  
  # vpc_config {
  #   security_group_ids = var.security_group_ids
  #   subnet_ids         = var.subnet_ids
  # }

  tags = merge(
    { "Name" = "${local.function_name}" },
    local.tags,
    # var.additional_tags
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
  inline_policy = concat( var.inline_policy,
    [
      {
        name = "AllowPermissions"
        policy = jsonencode(
          {
            Version = "2012-10-17",
            Statement = [
              {
                Action = [
                  "rds:ModifyDBCluster",
                ],
                Resource = [
                  "arn:aws:rds:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:cluster:${var.dbclusteridentifier}",
                ]
                Effect = "Allow"
              },
            ]
          }
        )
      },
    ],
    [
      {
        name = "ModulePermission"
        policy = jsonencode(
          {
            Version = "2012-10-17",
            Statement = [
              {
                Effect = "Allow"
                Action = [
                  "secretsmanager:DescribeSecret",
                  "secretsmanager:GetSecretValue",
                  "secretsmanager:PutSecretValue",
                  "secretsmanager:UpdateSecretVersionStage"
                ],
                Resource = var.secret_arn
              },
              {
                Effect = "Allow",
                Action = [
                  "secretsmanager:GetRandomPassword"
                ],
                Resource = "*"
              },
              {
                Effect = "Allow",
                Action = [
                  "ecs:ListClusters",
                  "ecs:ListTasks",
                  "ecs:DescribeTasks",
                  "ecs:DescribeTaskDefinition",
                ],
                Resource = "*"
              },
              {
                Effect = "Allow",
                Action = [
                  "ecs:UpdateService"
                ],
                Resource = "arn:aws:ecs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:service/${local.ecs_cluster_prefix}-${terraform.workspace}${local.tags.Zone}*-${local.tags.Project-Code}-*"
              },
            ]
          }
        )
      }
    ]
  )
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

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
  ] # "${var.managed_policy_arns}"

  dynamic "inline_policy" {
    for_each = local.inline_policy
    
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

resource "aws_lambda_permission" "allow_secret_manager" {
  statement_id  = "AllowExecutionFromSecretManager"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.simple_lambda.arn
  principal     = "secretsmanager.amazonaws.com"
}
