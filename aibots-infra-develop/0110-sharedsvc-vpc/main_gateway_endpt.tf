# There are only 2 types of FREE gateway endpoints.
# Let's just keep them all here to make things easier.
locals {
  gateway_endpoint_list = ["com.amazonaws.ap-southeast-1.s3"]
}

resource "aws_vpc_endpoint" "gateway_endpoints" {
  for_each = toset(local.gateway_endpoint_list)

  vpc_id       = local.vpc_id
  service_name = each.key

  route_table_ids = values(aws_route_table.project).*.id

  tags = merge(
    local.tags,
    { "Name" = "${local.vpce_name}${each.key}" }
  )
}

resource "aws_vpc_endpoint_policy" "gateway_endpoints" {
  for_each = {
    for entry in aws_vpc_endpoint.gateway_endpoints: "${entry.service_name}" => entry
    # if entry.private_dns_enabled == false # false if you are doing endpoint sharing, and you need all the route53
  }

  vpc_endpoint_id = aws_vpc_endpoint.gateway_endpoints[ each.value.service_name ].id
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      # {
      #   "Sid" : "AllowAll",
      #   "Effect" : "Allow",
      #   "Principal" : {
      #     "AWS" : "*"
      #   },
      #   "Action" : [
      #     "s3:*"
      #   ],
      #   "Resource": "*"
      # },
      { # https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html#edit-vpc-endpoint-policy-s3
        "Sid" : "AllowS3AccessInTrustedAccounts",
        "Effect" : "Allow",
        "Principal" : {
          "AWS" : "*"
        },
        "Action" : [
          "s3:*"
        ],
        "Resource": "*",
        "Condition": {
          "StringEquals": {
            "s3:ResourceAccount": [data.aws_caller_identity.current.account_id]
          }
        }
      },
      { # https://docs.aws.amazon.com/AmazonECR/latest/userguide/vpc-endpoints.html
        "Sid" : "AllowS3AccessForAWSECR",
        "Effect" : "Allow",
        "Principal" : {
          "AWS" : "*"
        },
        "Action" : [
          "s3:*"
        ],
        "Resource": ["arn:aws:s3:::prod-${data.aws_region.current.name}-starport-layer-bucket/*"],
      },
    ]
  })
}
