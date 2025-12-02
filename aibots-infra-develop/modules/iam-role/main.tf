# ref: https://www.terraform.io/docs/providers/aws/d/caller_identity.html
data "aws_caller_identity" "current" {}

locals {
  trust_relationship_arn = length(var.custom_trust_relationship_arn) > 0 ? var.custom_trust_relationship_arn : ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
}

# ref: https://www.terraform.io/docs/providers/aws/d/iam_policy_document.html
data "aws_iam_policy_document" "iam_trusted" {
  statement {
    actions = [var.trust_action]
    principals {
      type = var.principal_type
      # root looks scary but this is just a trust policy so that we can attach the actual
      # policy that allows sts:AssumeRole(default) to be exercised, this alone will not enable anything
      # to assume the role
      identifiers = local.trust_relationship_arn
    }

    # Only allow role to be assumed if Account equals is presented
    dynamic "condition" {
      for_each = length(var.condition_account_equal) > 0 ? [""] : []
      content {
        test     = "StringEquals"
        variable = "aws:SourceAccount"
        values   = [var.condition_account_equal]
      }
    }

    # Only allow role to be assumed if ARN like is presented
    dynamic "condition" {
      for_each = length(var.condition_arn_like) > 0 ? [""] : []
      content {
        test     = "ArnLike"
        variable = "aws:SourceArn"
        values   = var.condition_arn_like
      }
    }

    # Only allow role to be assumed if MFA token is present
    dynamic "condition" {
      for_each = length(var.condition_user_ids) > 0 ? [""] : []
      content {
        test     = "StringEquals"
        variable = "aws:userid"
        values   = var.condition_user_ids
      }
    }

    # Only allow role to be assumed if MFA token is present
    dynamic "condition" {
      for_each = var.condition_mfa ? [""] : []
      content {
        test     = "Bool"
        variable = "aws:MultiFactorAuthPresent"
        values = [
          "true",
        ]
      }
    }

    # Only allow role to be assumed if external id is provided and matched
    dynamic "condition" {
      for_each = length(var.condition_external_id) >= 12 ? [""] : []
      content {
        test     = "StringEquals"
        variable = "sts:ExternalId"
        values = [
          var.condition_external_id,
        ]
      }
    }

    dynamic "condition" {
      for_each = length(var.condition_ip_addresses_via_vpce) > 0 ? [""] : []
      content {
        test     = "IpAddress"
        variable = "aws:VpcSourceIp"
        values   = var.condition_ip_addresses_via_vpce
      }
    }

    # Only allow role to be assumed if traffic comes from specific IP addresses
    # This rule is ignored if the list is empty.
    dynamic "condition" {
      for_each = length(var.condition_ip_addresses) > 0 ? [""] : []
      content {
        test     = "IpAddress"
        variable = "aws:SourceIp"
        values   = var.condition_ip_addresses
      }
    }

    # Only allow role to be assumed for identity provider audience
    dynamic "condition" {
      for_each = var.condition_identity_providers
      content {
        test     = var.condition_identity_providers["aud"]["test"]
        variable = var.condition_identity_providers["aud"]["claim_key"]
        values   = ["${var.condition_identity_providers["aud"]["claim_value"]}"]
      }

    }

    # Only allow role to be assumed for identity provider subject
    dynamic "condition" {
      for_each = var.condition_identity_providers
      content {
        test     = var.condition_identity_providers["sub"]["test"]
        variable = var.condition_identity_providers["sub"]["claim_key"]
        values   = ["${var.condition_identity_providers["sub"]["claim_value"]}"]
      }
    }

  }
}

# ref: https://www.terraform.io/docs/providers/aws/r/iam_role.html
resource "aws_iam_role" "iam_role" {
  name                  = var.name
  path                  = var.path
  description           = var.description
  assume_role_policy    = data.aws_iam_policy_document.iam_trusted.json
  max_session_duration  = var.max_session_duration
  force_detach_policies = var.force_detach_policies

  tags = var.tags
}

# Only create the custom inline policy for this role if it's not empty
resource "aws_iam_role_policy" "custom_policy" {
  count = var.custom_policy != "" ? 1 : 0

  name   = var.custom_policy_name
  role   = aws_iam_role.iam_role.name
  policy = var.custom_policy
}

# Create as managed policies and attach accordingly
resource "aws_iam_policy" "managed_policies" {
  for_each = var.managed_policies

  name   = "${var.name}-${each.key}-policy"
  policy = each.value

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "managed_policies" {
  for_each = var.managed_policies

  role       = aws_iam_role.iam_role.name
  policy_arn = aws_iam_policy.managed_policies[each.key].arn
}

# Maps the given list of existing policies to the role
resource "aws_iam_role_policy_attachment" "attach_policy" {
  role       = aws_iam_role.iam_role.name
  for_each   = var.attach_policies
  policy_arn = each.value
}

# creates instance profile if instance_profile is true
resource "aws_iam_instance_profile" "instance_profile" {
  count = var.instance_profile == true ? 1 : 0

  name = var.name
  role = aws_iam_role.iam_role.name

  tags = var.tags
}
