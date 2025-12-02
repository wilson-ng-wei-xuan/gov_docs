locals {
  apigw_name = substr( "api-${var.tags.environment}${var.tags.zone}-${var.name}", 0, 1024)
}

resource "aws_api_gateway_rest_api" "apigw_rest_api" {
  name        = "${local.apigw_name}"
  description = "APIGW for ${var.name} in ${var.tags.zone}"

  endpoint_configuration {
    types = ["PRIVATE"]
    vpc_endpoint_ids = var.apigw_allowed_vpce
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(
    { "Name" = "${local.apigw_name}" },
    local.tags,
    var.additional_tags
  )
}

# resource "aws_api_gateway_request_validator" "apigw_request_validator" {
#   name                        = "Validate Body"
#   rest_api_id                 = aws_api_gateway_rest_api.apigw_rest_api.id
#   validate_request_body       = true
#   validate_request_parameters = true
# }

resource "aws_api_gateway_rest_api_policy" "apigw_policy" {
  rest_api_id = aws_api_gateway_rest_api.apigw_rest_api.id

  policy = <<EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": "*",
        "Action": "execute-api:Invoke",
        "Resource": [
          "${aws_api_gateway_rest_api.apigw_rest_api.execution_arn}/*"
        ],
        "Condition" : {
          "StringEquals": {
            "aws:SourceVpce": ["${join("\",\"",var.apigw_allowed_vpce)}"]
          }
        }
      }
    ]
  }
  EOF
}