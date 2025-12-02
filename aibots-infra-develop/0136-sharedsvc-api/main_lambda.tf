######################################################################################
# use Template to render the variables in the env file
data "template_file" "env_variables" {
  for_each = { for entry in var.pte_api: "${entry.name}" => entry }
  template    = file("${path.module}/source/lambda/${each.value.name}.environment.json")
  # count       = length(var.pte_api)
  # template    = file("${path.module}/source/lambda/${var.pte_api[count.index].name}.environment.json")

  vars        = { # these are the variables to render
      SHAREDSVC_EMAIL__BUCKET = data.aws_s3_bucket.email.id
  }
}

######################################################################################
# use Template to render the variables in the policy file
data "template_file" "policy" {
  for_each = { for entry in var.pte_api: "${entry.name}" => entry }
  template    = file("${path.module}/source/lambda/${each.value.name}.policy.json")
  # count       = length(var.pte_api)
  # template    = file("${path.module}/source/lambda/${var.pte_api[count.index].name}.policy.json")

  vars        = { # these are the variables to render
      SHAREDSVC_EMAIL__BUCKET_arn = data.aws_s3_bucket.email.arn
  }
}

######################################################################################
module "simple_lambda" {
  for_each = { for entry in var.pte_api: "${entry.name}" => entry }

  source = "../modules/lambda"

  # The variables required by your module e.g shown below
  function_name = "${var.project_code}-${var.project_desc}-${each.value.name}"
  memory_size = 128
  security_group_ids = [ data.aws_security_group.sharedsvc_ez["${local.secgrp_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id ]
  # subnet_ids = [ data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-${local.az_deployment}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]
  subnet_ids = [ data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-a-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
                 data.aws_subnet.sharedsvc_ez["${local.subnet_prefix}-b-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id, ]
  filename= "${path.module}/source/lambda/${each.value.name}.zip"
  handler = "lambda_function.lambda_handler"
  timeout = 60

  runtime = local.default_lambda_runtime
  layers = [ data.aws_lambda_layer_version.LambdaInsightsExtension.id ]

  environment_variables = jsondecode( data.template_file.env_variables[ each.value.name ].rendered )

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
  ]

  inline_policy = [
    {
      name = "AllowPermissions"
      policy = data.template_file.policy[ each.value.name ].rendered
    },
  ]

  retention_in_days = each.value.retention_in_days
  destination_arn = data.aws_lambda_function.notification.arn

  tags = local.tags
}