##
## Cloudwatch specific variables
##
variable "filter_pattern" {
  type        = string
  default     = "?\"[NOTIFY]\" ?\"[ERROR]\" ?\"[WARNING]\" ?\"[WARN]\" ?\"[CRITICAL]\" ?\"Task timed out\" ?\"AccessDenied\" ?\"signal: killed\""
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


variable "runtime" {
  type        = string
  default     = "python3.12"
  description = <<EOT
    (Required) Identifier of the Lambda Function runtime.
    Refer to: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
  EOT
}