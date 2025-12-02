resource "aws_opensearchserverless_security_policy" "encryption" {
  # name length <= 32
  name        = "${local.opensearch_name}"
  type        = "encryption"
  description = "encryption policy for ${local.opensearch_name}"
  policy = jsonencode({
    Rules = [
      {
        Resource = [
          "collection/${local.opensearch_name}*"
        ],
        ResourceType = "collection"
      }
    ],
    AWSOwnedKey = true
  })
}

resource "aws_opensearchserverless_collection" "vectorsearch" {
  count = var.aoss_count
  depends_on = [ aws_opensearchserverless_security_policy.encryption ]

  # name length <= 32
  name = "${local.opensearch_name}${format("%02s", count.index+1)}"
  description = "Collection for ${local.opensearch_name}${format("%02s", count.index+1)}"
  type = "VECTORSEARCH"

  tags = merge(
    local.tags,
    { Name = "${local.opensearch_name}${format("%02s", count.index+1)}" }
  )
}

################################################################################
# https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-network.html
################################################################################
resource "aws_opensearchserverless_security_policy" "network" {
  # name length <= 32
  name        = "${local.opensearch_name}"
  type        = "network"
  description = "dashboard and collection access for ${local.opensearch_name}"
  policy = jsonencode([
    {
      Description = "VPC access for ${var.project_code}-${var.project_desc}",
      Rules = [
        {
          ResourceType = "collection",
          Resource = [
            "collection/${local.opensearch_name}*"
          ]
        }
      ],
      AllowFromPublic = false,
      SourceVPCEs = [
        aws_opensearchserverless_vpc_endpoint.vectorsearch.id
      ]
    },
    {
      Description = "dashboard access for ${local.opensearch_name}",
      Rules = [
        {
          ResourceType = "dashboard"
          Resource = [
            "collection/${local.opensearch_name}*"
          ]
        }
      ],
      AllowFromPublic = true
    }
  ])
}

################################################################################

resource "aws_security_group" "vectorsearch" {
  name        = local.secgrp_name
  description = "${var.project_code}-${var.project_desc}"
  vpc_id      = data.aws_vpc.aibots_ez.id

  tags = merge(
    local.tags,
    { "Name" = local.secgrp_name }
  )
}

resource "aws_vpc_security_group_egress_rule" "vectorsearch" {
  security_group_id = aws_security_group.vectorsearch.id

  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
  description = "Allow 443 outbound to Opensearch"
}

################################################################################

resource "aws_opensearchserverless_vpc_endpoint" "vectorsearch" {
  name               = "${var.project_code}-${var.project_desc}"
  vpc_id             = data.aws_vpc.aibots_ez.id
  subnet_ids         = [
                        data.aws_subnet.aibots_ez["${local.subnet_prefix}-a-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
                        data.aws_subnet.aibots_ez["${local.subnet_prefix}-b-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
                       ]
  security_group_ids = [
                        aws_security_group.vectorsearch.id,
                        data.aws_security_group.aibots_ez["${local.secgrp_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}"].id,
                       ]
}

resource "aws_vpc_endpoint_policy" "interface_endpt" {
  vpc_endpoint_id = aws_opensearchserverless_vpc_endpoint.vectorsearch.id
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid": "Allow-Account-Resources",
        "Effect" : "Allow",
        "Principal" : "*",
        "Action": "*",
        "Resource" : "*",
        "Condition": {
          "StringEquals": {
            "aws:ResourceAccount": [
              data.aws_caller_identity.current.account_id
            ]
          }
        }
      }
    ]
  })
}