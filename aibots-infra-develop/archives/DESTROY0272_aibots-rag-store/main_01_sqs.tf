module "sqs" {
  for_each  = { for entry in var.process: "${entry.name}" => entry }

  source = "git@sgts.gitlab-dedicated.com:wog/gvt/dsaid-st/atlas/terraform/modules.git//sqs"
  # source = "../../../Atlas/Infra/modules/lambda"
  # version = "~>3.0"

  # The variables required by your module e.g shown below
  name = "${var.project_code}-${var.project_desc}-${each.value.name}"
  account_id = data.aws_caller_identity.current.account_id
  # sqs_vpce_id = data.aws_vpc_endpoint.sqs.id
  redrive_policy_maxReceiveCount = var.redrive_policy_maxReceiveCount # number of tries before sending to DLQ
  visibility_timeout_seconds = var.timeout * 2 #  IF message failed by GPT throttle, makes it invisible before it gets process again.

  tags = local.tags
}