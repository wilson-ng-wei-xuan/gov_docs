resource "random_string" "this" {
  length  = 10
  special = false
  upper   = false
}

##################################################
locals {
  path = split("/", path.cwd)[length(split("/", path.cwd))-1]

  # for resources deployed in single AZ, e.g. endpoints.
  # note that this only helps with swinging the AZ.
  # if you want to change from single to dual AZ, you will need to manually search and change.
  az_deployment = "a"

  # resources naming prefix for standardisation
  alb_prefix = "alb" # used by listener_rule_name and target_grp_name
  # apigw is in module
  cognito_prefix      = "cognito"
  cw_event_prefix     = "cw-event"
  ddb_prefix          = "dynamodb"
  ec2_prefix          = "vm"
  ecr_prefix          = "ecr"
  ecs_cluster_prefix  = "ecs-cluster"
  ecs_service_prefix  = "ecs-svc"
  ecs_task_prefix     = "ecs-task"
  iam_role_prefix     = "iam-role"
  iam_policy_prefix   = "iam-policy"
  igw_prefix          = "igw"
  kms_prefix          = "key"
  lambda_prefix       = "compute-lambda"
  lambda_layer_prefix = "lambdalayer"
  lb_rule_prefix      = "rule"
  nacl_prefix         = "nacl"
  nat_prefix          = "nat"
  nfw_prefix          = "nfw"
  para_store_prefix   = "para"
  peering_prefix      = "peer"
  routetable_prefix   = "rt"
  s3_prefix           = "sst-s3"
  secgrp_prefix       = "sgrp"
  secret_prefix       = "secret"
  sns_prefix          = "sns"
  sqs_prefix          = "sqs"
  subnet_prefix       = "sub"
  target_grp_prefix   = "tg"
  tgw_prefix          = "tgw"
  tgw_attach_prefix   = "tgw-attach"
  vpc_prefix          = "vpc"
  vpce_prefix         = "vpce"
  waf_prefix          = "waf"

  # naming standardisation
  # prefix - agency_code - dept - terraform.workspace zone tier - project_code project_desc

  #######################################################################
  # These are zoneless-tierless resources.                              #
  #######################################################################
  layer_name   = substr("${local.lambda_layer_prefix}-${terraform.workspace}-", 0, 64)
  peering_name = substr("${local.peering_prefix}-${terraform.workspace}-", 0, 128)

  #######################################################################
  # These are tierless resources.                                       #
  #######################################################################
  igw_name    = substr("${local.igw_prefix}-${terraform.workspace}${var.zone}-${var.project_code}", 0, 255)
  tgw_name    = substr("${local.tgw_prefix}-${terraform.workspace}${var.zone}-${var.project_code}", 0, 256)
  vpc_name    = substr("${local.vpc_prefix}-${terraform.workspace}${var.zone}-${var.project_code}", 0, 1024)
  kms_name    = substr("${local.kms_prefix}-${terraform.workspace}${var.zone}-${var.project_code}${var.project_desc}-${random_string.this.result}", 0, 256)
  policy_name = substr("${local.iam_policy_prefix}-${terraform.workspace}${var.zone}-${var.project_code}${var.project_desc}", 0, 128)
  role_name   = substr("${local.iam_role_prefix}-${terraform.workspace}${var.zone}-${var.project_code}${var.project_desc}", 0, 64)

  #######################################################################
  # These are super short naming.                                       #
  #######################################################################
  listener_rule_name = substr("${local.lb_rule_prefix}-${local.alb_prefix}-${var.project_code}${var.project_desc}", 0, 40)
  target_grp_name    = substr("${local.target_grp_prefix}-${local.alb_prefix}-${var.project_code}${var.project_desc}", 0, 32)

  #######################################################################
  # These are typical resources.                                        #
  # while some global/project might not have a tier, but go get a life. #
  #######################################################################
  # alb is in module
  # apigw is in module
  # cw_log_group_name   = "/aws/vpc-flow-log/${local.cw_log_group_name}"
  # cw_log_group_name   = "/ecs/fargate-task/${local.cw_log_group_name}"
  cognito_name      = substr("${local.cognito_prefix}-${terraform.workspace}${var.zone}-${var.project_code}${var.project_desc}", 0, 128)
  cw_log_group_name = substr("${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 512)
  cw_alarm_name     = substr("${local.cw_event_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 1024)
  ddb_name          = substr("${local.ddb_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 255)
  ecs_cluster_name  = substr("${local.ecs_cluster_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 255)
  ecs_service_name  = substr("${local.ecs_service_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 255)
  ecs_task_name     = substr("${local.ecs_task_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 255)
  lambda_name       = substr("${local.lambda_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 64)
  nat_name          = substr("${local.nat_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 255)
  nfw_name          = substr("${local.nfw_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 255)
  para_store_name   = substr("${local.para_store_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 900)
  secgrp_name       = substr("${local.secgrp_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 255)
  secret_name       = substr("${local.secret_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 512)
  sns_name          = substr("${local.sns_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 256)
  tgw_attach_name   = substr("${local.tgw_attach_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}", 0, 256)
  vpce_name         = substr("${local.vpce_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}-", 0, 255)
  waf_name          = substr("${local.waf_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 255)

  # the list of standard tagging to give context to the resources
  tags = {
    "terraform"    = "true"
    "agency-code"  = "${var.agency_code}"
    "dept"         = "${var.dept}"
    "project-code" = "${var.project_code}"
    "region"       = "${data.aws_region.current.name}"
    "environment"  = "${terraform.workspace}"
    "zone"         = "${var.zone}"
    "tier"         = "${var.tier}"
    "ops:end-date" = "${var.opsend-date}"
  }
}
