##################################################
locals {
  path = split("/", path.cwd)[length(split("/", path.cwd)) - 1]

  route53_zone_prefix = "${terraform.workspace}" == "prd" ? "" : "${terraform.workspace}."

  # for resources deployed in single AZ, e.g. endpoints.
  # note that this only helps with swinging the AZ.
  # if you want to change from single to dual AZ, you will need to manually search and change.
  az_deployment = "a"

  # resources naming prefix for standardisation
  # you need these prefixes for the output file.
  alarm_prefix = "alarm"
  alb_prefix   = "alb" # used by listener_rule_name and target_grp_name
  nlb_prefix   = "nlb" # used by listener_rule_name and target_grp_name
  # apigw is in module
  backup_plan_prefix  = "backupplan"
  backup_vault_prefix = "backupvault"
  cognito_prefix      = "cognito"
  ddb_prefix          = "dynamodb"
  docdb_prefix        = "docdb"
  ec2_prefix          = "vm"
  ecr_prefix          = "ecr"
  ecs_cluster_prefix  = "ecscluster"
  ecs_service_prefix  = "ecssvc"
  ecs_task_prefix     = "ecstask"
  event_prefix        = "event"
  iam_oidc_prefix     = "iamoidc"
  iam_policy_prefix   = "iampolicy"
  iam_role_prefix     = "iamrole"
  iam_user_prefix     = "iamuser"
  igw_prefix          = "igw"
  kms_prefix          = "key"
  lambda_prefix       = "lambda"
  lambda_layer_prefix = "lambdalayer"
  lb_rule_prefix      = "rule"
  nacl_prefix         = "nacl"
  nat_prefix          = "nat"
  nfw_prefix          = "nfw"
  opensearch_prefix   = "aoss"
  para_store_prefix   = "param"
  peering_prefix      = "peer"
  redis_prefix        = "redis"
  routetable_prefix   = "rt"
  s3_prefix           = "s3"
  secgrp_prefix       = "sgrp"
  secret_prefix       = "secret"
  sns_prefix          = "sns"
  sqs_prefix          = "sqs"
  subnet_prefix       = "sub"
  target_grp_prefix   = "tg"
  tgw_prefix          = "tgw"
  tgw_attach_prefix   = "tgwattach"
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
  kms_name    = substr("${local.kms_prefix}-${terraform.workspace}${var.zone}-${var.project_code}${var.project_desc}", 0, 256)
  policy_name = substr("${local.iam_policy_prefix}-${terraform.workspace}${var.zone}-${var.project_code}-${var.project_desc}", 0, 128)
  oidc_name   = substr("${local.iam_oidc_prefix}-${terraform.workspace}${var.zone}-${var.project_code}-${var.project_desc}", 0, 64)
  role_name   = substr("${local.iam_role_prefix}-${terraform.workspace}${var.zone}-${var.project_code}-${var.project_desc}", 0, 64)
  user_name   = substr("${local.iam_user_prefix}-${terraform.workspace}${var.zone}-${var.project_code}-${var.project_desc}", 0, 64)

  #######################################################################
  # These are super short naming.                                       #
  #######################################################################
  alb_lsnr_rule_name = substr("${local.lb_rule_prefix}-${local.alb_prefix}-${var.project_code}-${var.project_desc}", 0, 40)
  nlb_lsnr_rule_name = substr("${local.lb_rule_prefix}-${local.nlb_prefix}-${var.project_code}-${var.project_desc}", 0, 40)
  alb_tg_name        = substr("${local.target_grp_prefix}-${local.alb_prefix}-${var.project_code}-${var.project_desc}", 0, 32)
  nlb_tg_name        = substr("${local.target_grp_prefix}-${local.nlb_prefix}-${var.project_code}-${var.project_desc}", 0, 32)
  opensearch_name    = substr("${local.opensearch_prefix}-${terraform.workspace}-${var.project_code}-${var.project_desc}", 0, 32)
  # due to the very limited length, opensearch_data_access cannot accomodate the prefix.
  # this is only meant for Data access policies
  # Encryption policies and Network policies must match the collection name, i.e. opensearch_name
  opensearch_data_access_name = substr("${terraform.workspace}-${var.project_code}-${var.project_desc}", 0, 32)

  #######################################################################
  # These are typical resources.                                        #
  # while some global/project might not have a tier, but go get a life. #
  #######################################################################
  # alb is in module
  # apigw is in module
  # cw_log_group_name   = "/aws/vpc-flow-log/${local.cw_log_group_name}"
  # cw_log_group_name   = "/ecs/fargate-task/${local.cw_log_group_name}"
  alarm_name = substr("${local.alarm_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 1024)
  alb_name   = substr("${local.alb_prefix}-${local.tags.Environment}${var.zone}${var.tier}", 0, 32)

  backup_plan_name  = substr("${local.backup_plan_prefix}-${terraform.workspace}${var.zone}-${var.project_code}", 0, 50)
  backup_vault_name = substr("${local.backup_vault_prefix}-${terraform.workspace}${var.zone}-${var.project_code}", 0, 50)

  cognito_name     = substr("${local.cognito_prefix}-${terraform.workspace}${var.zone}-${var.project_code}-${var.project_desc}", 0, 128)
  cw_log_name      = substr("${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 512)
  ddb_name         = substr("${local.ddb_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 255)
  docdb_name       = substr("${local.docdb_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}-${var.project_desc}", 0, 50)
  ecr_name         = substr("${local.ecr_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}-${var.project_desc}", 0, 256)
  ecs_cluster_name = substr("${local.ecs_cluster_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 255)
  ecs_service_name = substr("${local.ecs_service_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 255)
  ecs_task_name    = substr("${local.ecs_task_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}-${var.project_desc}", 0, 255)
  cwevent_name     = substr("cw${local.event_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}-${var.project_desc}", 0, 1024)
  s3event_name     = substr("s3${local.event_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}", 0, 1024)
  lambda_name      = substr("${local.lambda_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 64)
  nat_name         = substr("${local.nat_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 255)
  nfw_name         = substr("${local.nfw_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 255)
  para_store_name  = substr("${local.para_store_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}-${var.project_desc}", 0, 900)
  redis_name       = substr("${local.redis_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}-${var.project_desc}", 0, 40)
  secgrp_name      = substr("${local.secgrp_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}-${var.project_desc}", 0, 255)
  secret_name      = substr("${local.secret_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}", 0, 512)
  sns_name         = substr("${local.sns_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}-${var.project_desc}", 0, 256)
  sqs_name         = substr("${local.sqs_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}-${var.project_desc}", 0, 256)
  tgw_attach_name  = substr("${local.tgw_attach_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}", 0, 256)
  vpce_name        = substr("${local.vpce_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}-", 0, 255)
  waf_name         = substr("${local.waf_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 255)

  # the list of standard tagging to give context to the resources
  tags = {
    "Terraform" = "true"
    # "Agency-Code"  = "${var.agency_code}" == "" ? "na" : "${var.agency_code}"
    # "Dept"         = "${var.dept}" == "" ? "na" : "${var.dept}"
    "Agency-Code"  = "gvt"
    "Dept"         = "gdp"
    "Project-Code" = "${var.project_code}" == "" ? "na" : "${var.project_code}"
    "Project-Desc" = "${var.project_desc}" == "" ? "na" : "${var.project_desc}"
    "Region"       = "${data.aws_region.current.name}"
    "Environment"  = "${terraform.workspace}"
    "Zone"         = "${var.zone}" == "" ? "na" : "${var.zone}"
    "Tier"         = "${var.tier}" == "" ? "na" : "${var.tier}"
    "Ops-EndDate"  = "${var.ops_enddate}" == "" ? "na" : "${var.ops_enddate}"
  }

  # cctags = [
  #   { "key" = "Terraform"   , "value" = "true" },
  #   { "key" = "Agency-Code" , "value" = "${local.tags.Agency-Code}" },
  #   { "key" = "Dept"        , "value" = "${local.tags.Dept}" },
  #   { "key" = "Project-Code", "value" = "${local.tags.Project-Code}" },
  #   { "key" = "Project-Desc", "value" = "${local.tags.Project-Desc}" },
  #   { "key" = "Region"      , "value" = "${local.tags.Region}" },
  #   { "key" = "Environment" , "value" = "${local.tags.Environment}" },
  #   { "key" = "Zone"        , "value" = "${local.tags.Zone}" },
  #   { "key" = "Tier"        , "value" = "${local.tags.Tier}" },
  #   { "key" = "Ops-EndDate" , "value" = "${local.tags.Ops-EndDate}" }
  # ]
}