##################################################
locals {
  # path = split("/", path.cwd)[length(split("/", path.cwd))-1]

  # route53_zone_prefix = "${terraform.workspace}" == "prd" ? "" : "${terraform.workspace}."

  # # for resources deployed in single AZ, e.g. endpoints.
  # # note that this only helps with swinging the AZ.
  # # if you want to change from single to dual AZ, you will need to manually search and change.
  # az_deployment = "a"

  # resources naming prefix for standardisation
  # you need these prefixes for the output file.
  alarm_prefix        = "alarm"
  alb_prefix = "alb" # used by listener_rule_name and target_grp_name
  nlb_prefix = "nlb" # used by listener_rule_name and target_grp_name
  # apigw is in module
  cognito_prefix      = "cognito"
  ddb_prefix          = "dynamodb"
  docdb_prefix        = "docdb"
  ec2_prefix          = "vm"
  ecr_prefix          = "ecr"
  ecs_cluster_prefix  = "ecscluster"
  ecs_service_prefix  = "ecssvc"
  ecs_task_prefix     = "ecstask"
  event_prefix        = "event"
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
  para_store_prefix   = "param"
  peering_prefix      = "peer"
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
  layer_name   = substr("${local.lambda_layer_prefix}-${local.tags.Environment}-", 0, 64)
  peering_name = substr("${local.peering_prefix}-${local.tags.Environment}-", 0, 128)

  #######################################################################
  # These are tierless resources.                                       #
  #######################################################################
  igw_name    = substr("${local.igw_prefix}-${local.tags.Environment}${local.tags.Zone}-", 0, 255)
  tgw_name    = substr("${local.tgw_prefix}-${local.tags.Environment}${local.tags.Zone}-", 0, 256)
  vpc_name    = substr("${local.vpc_prefix}-${local.tags.Environment}${local.tags.Zone}-", 0, 1024)
  kms_name    = substr("${local.kms_prefix}-${local.tags.Environment}${local.tags.Zone}-", 0, 256)
  policy_name = substr("${local.iam_policy_prefix}-${local.tags.Environment}${local.tags.Zone}", 0, 128)
  role_name   = substr("${local.iam_role_prefix}-${local.tags.Environment}${local.tags.Zone}", 0, 64)
  user_name   = substr("${local.iam_user_prefix}-${local.tags.Environment}${local.tags.Zone}", 0, 64)

  #######################################################################
  # These are super short naming.                                       #
  #######################################################################
  # alb_lsnr_rule_name = substr("${local.lb_rule_prefix}-${local.alb_prefix}-${local.tags.Project-Code}-${local.tags.Project-Desc}", 0, 40)
  # nlb_lsnr_rule_name = substr("${local.lb_rule_prefix}-${local.nlb_prefix}-${local.tags.Project-Code}-${local.tags.Project-Desc}", 0, 40)
  # alb_tg_name    = substr("${local.target_grp_prefix}-${local.alb_prefix}-${local.tags.Project-Code}-${local.tags.Project-Desc}", 0, 32)
  # nlb_tg_name    = substr("${local.target_grp_prefix}-${local.nlb_prefix}-${local.tags.Project-Code}-${local.tags.Project-Desc}", 0, 32)
  alb_lsnr_rule_name = substr("${local.lb_rule_prefix}-${local.alb_prefix}", 0, 40)
  nlb_lsnr_rule_name = substr("${local.lb_rule_prefix}-${local.nlb_prefix}", 0, 40)
  alb_tg_name    = substr("${local.target_grp_prefix}-${local.alb_prefix}", 0, 32)
  nlb_tg_name    = substr("${local.target_grp_prefix}-${local.nlb_prefix}", 0, 32)


  #######################################################################
  # These are typical resources.                                        #
  # while some global/project might not have a tier, but go get a life. #
  #######################################################################
  tier_name = local.tags.Tier == "na" ? "" : local.tags.Tier
  # alb is in module
  # apigw is in module
  # cw_log_group_name   = "/aws/vpc-flow-log/${local.cw_log_group_name}"
  # cw_log_group_name   = "/ecs/fargate-task/${local.cw_log_group_name}"
  alarm_name        = substr("${local.alarm_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}", 0, 1024)
  # alb_name          = substr("${local.alb_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}", 0, 32)
  cognito_name      = substr("${local.cognito_prefix}-${local.tags.Environment}${local.tags.Zone}-", 0, 128)
  cw_log_name       = substr("${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}", 0, 512)
  ddb_name          = substr("${local.ddb_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}-", 0, 255)
  docdb_name        = substr("${local.docdb_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}-", 0, 50)
  ecr_name          = substr("${local.ecr_prefix}-${local.tags.Environment}-${local.tags.Zone}${local.tags.Tier}-", 0, 256)
  ecs_cluster_name  = substr("${local.ecs_cluster_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}", 0, 255)
  ecs_service_name  = substr("${local.ecs_service_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}", 0, 255)
  ecs_task_name     = substr("${local.ecs_task_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}", 0, 255)
  cwevent_name      = substr("cw${local.event_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}", 0, 1024)
  s3event_name      = substr("s3${local.event_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}", 0, 1024)
  lambda_name       = substr("${local.lambda_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tier_name}", 0, 64)
  nat_name          = substr("${local.nat_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}-", 0, 255)
  nfw_name          = substr("${local.nfw_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}-", 0, 255)
  para_store_name   = substr("${local.para_store_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}", 0, 900)
  secgrp_name       = substr("${local.secgrp_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}-", 0, 255)
  secret_name       = substr("${local.secret_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}", 0, 512)
  sns_name          = substr("${local.sns_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}-", 0, 256)
  sqs_name          = substr("${local.sqs_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}", 0, 256)
  tgw_attach_name   = substr("${local.tgw_attach_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}-", 0, 256)
  vpce_name         = substr("${local.vpce_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}-${local.tags.Project-Code}", 0, 255)
  waf_name          = substr("${local.waf_prefix}-${local.tags.Environment}${local.tags.Zone}${local.tags.Tier}-", 0, 255)
}