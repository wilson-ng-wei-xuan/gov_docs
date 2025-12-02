variable "function_name" {
  type        = string
  description = <<EOT
    (Required) The name of the resource, e.g. mylambda. This will be used in the name of the resources.
  EOT
}
##
## Cloudwatch specific variables
##
variable "retention_in_days" {
  type        = number
  default     = 365
  description = <<EOT
    (Optional) Specifies the number of days you want to retain log events in the specified log group.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group
  EOT
}

variable "destination_arn" {
  type        = string
  default     = null
  description = <<EOT
    The ARN of the destination to deliver matching log events to. Kinesis stream or Lambda function ARN.
    If not provided, the subscription filter will not be created.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_subscription_filter
  EOT
}

variable "filter_pattern" {
  type        = string
  default     = "?\"[NOTIFY]\" ?\"[ERROR]\" ?\"[WARNING]\" ?\"[WARN]\" ?\"[CRITICAL]\" ?\"Task timed out\" ?\"signal: killed\""
  description = <<EOT
    CloudWatch Logs filter pattern for subscribing to a filtered stream of log events.
    Since we are deploying lambda, we just default it to something that is more Lambda.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_subscription_filter#filter_pattern
  EOT
}

##
## IAM specific variables
##
variable "managed_policy_arns" {
  type        = list(string)
  default     = []
  description = <<EOT
    (Optional) Set of exclusive IAM managed policy ARNs to attach to the IAM role.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role
  EOT
}

variable "inline_policy" {
  type        = list( any )
  default     = []
  description = <<EOT
    (Optional) Inline policy to attach to the IAM role.
    inline_policy = [
      {
        name = "policy_name"
        policy = jsonencode(
          {
            Version = "2012-10-17",
            Statement = [
              {
                Action = [
                  "logs:CreateLogStream",
                  "logs:PutLogEvents",
                ],
                Resource = [
                    "resource.arn",
                ]
                Effect = "Allow"
              },
              {
                Action = "ecr:GetAuthorizationToken",
                Resource = "*",
                Effect = "Allow"
              },
            ]
          }
        )
      },
      {
        name = "policy_name"
        policy = jsonencode(
          {
            Blah = "blah"
          }
        )
      }
    ]
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role
  EOT
}

variable "permissions_boundary" {
  type        = string
  default     = null
  description = <<EOT
    (Optional) ARN of the policy that is used to set the permissions boundary for the role.
    You generally do not need this unless you are still in GCC1.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role
  EOT
}

##
## Lambda specific variables
##
variable "security_group_ids" {
  type        = list(string)
  description = <<EOT
    (Required) List of security group IDs associated with the Lambda, e.g. ['sg-000','sg-999'], to deploy the lambda in VPC.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
  EOT
}

variable "subnet_ids" {
  type        = list(string)
  description = <<EOT
    (Required) List of subnet IDs associated with the Lambda function, e.g. ['subnet-000','subnet-999'], to deploy the lambda in VPC.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
  EOT
}

# variable "filename" {
#   type        = string
#   description = <<EOT
#     (Required) Path to the Lambda Function deployment package within the local filesystem.
#     Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
#   EOT
# }

variable "memory_size" {
  type        = number
  default     = 128
  description = <<EOT
    (Optional) Amount of memory in MB your Lambda Function can use at runtime.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
  EOT
}

variable "timeout" {
  type        = number
  default     = 3
  description = <<EOT
    (Optional) Amount of time your Lambda Function has to run in seconds.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
  EOT
}

variable "environment_variables" {
  type        = any
  default     = { "default_key":"default value" }
  description = <<EOT
    (Optional) Map of environment variables that are accessible from the function code during execution.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
  EOT
}

variable "layers" {
  type        = list(string)
  default     = []
  description = <<EOT
    (Optional) List of Lambda Layer Version ARNs (maximum of 5) to attach to your Lambda Function
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
  EOT
}

variable "handler" {
  type        = string
  description = <<EOT
    (Required) Function entrypoint in your code.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
  EOT
}

variable "runtime" {
  type        = string
  default     = "python3.12"
  description = <<EOT
    (Required) Identifier of the Lambda Function runtime.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
  EOT
}

variable "secret_arn" {
  type        = string
  description = <<EOT
    The Secret ARN to rotate.
  EOT
}

variable "dbclusteridentifier" {
  type        = string
  description = <<EOT
    The DBClusterIdentifier.
  EOT
}