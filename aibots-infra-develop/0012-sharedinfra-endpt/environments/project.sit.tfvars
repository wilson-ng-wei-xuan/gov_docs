# update your project specific environmental 
interface_endpts = [
  {
    service_name  = "com.amazonaws.ap-southeast-1.logs", # use by application logs
  },
  {
    service_name  = "com.amazonaws.ap-southeast-1.secretsmanager", # use by docdb
  },
  {
    service_name  = "com.amazonaws.ap-southeast-1.ecr.api", # use by fargate
  },
  {
    service_name  = "com.amazonaws.ap-southeast-1.ecr.dkr", # use by fargate
  },
  {
    service_name  = "com.amazonaws.ap-southeast-1.ecs", # for restarting the task
  },
  {
    service_name  = "com.amazonaws.ap-southeast-1.sqs", # use by batch fanout
  },
  {
    service_name  = "com.amazonaws.ap-southeast-1.ssm", # for parameter store, via Systems Manager service.
  },
  {
    service_name  = "com.amazonaws.ap-southeast-1.bedrock-runtime", # for bedrock api calls.
  },
#  {
#    service_name  = "com.amazonaws.vpce.ap-southeast-1.vpce-svc-0cd4f01b48391d719",
#    name          = "api.cloak.gov.sg",
#    restrict_oubound    = false # security requires us to restrict outbound, but service endpoints cannot lockdown.
#    private_dns_enabled = true  # Private DNS can only be enabled after the endpoint connection is accepted by the owner
#                                # true to use VPCE default dns, false if you want to share endpoints
#  },
#  {
#    service_name  = "com.amazonaws.ap-southeast-1.ec2messages", # For cloud 9 Systems Manager uses this to make calls from SSM Agent to the Systems Manager service.
#  },
#  {
#    service_name  = "com.amazonaws.ap-southeast-1.ssmmessages", # For cloud 9 This is required to connect to your instances using Session Manager.
#  },
  # "com.amazonaws.ap-southeast-1.sns", # use by cw_alarm_sns_topic_arn, aws service to service no need endpoints.
  # "com.amazonaws.ap-southeast-1.sts",
  # "com.amazonaws.ap-southeast-1.sagemaker.runtime",
  # "com.amazonaws.ap-southeast-1.execute-api",
]