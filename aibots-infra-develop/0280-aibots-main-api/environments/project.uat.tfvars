# update your project specific environmental 

cpu = 256

memory = 512 # 512

desired_count = 0 # will set the value to min_capacity
min_capacity = 1
max_capacity = 20 # 2

scale_in_cooldown = 0 # 0 will take 2*var.health_check_grace_period_seconds
scale_out_cooldown = 0 # 0 will take 2*var.health_check_grace_period_seconds

health_check_grace_period_seconds = 60

# task_role_managed_policy_arns = [
#   "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
#   "arn:aws:iam::aws:policy/AmazonS3FullAccess",
#   "arn:aws:iam::aws:policy/AmazonSESFullAccess",
#   "arn:aws:iam::aws:policy/AmazonSQSFullAccess",
#   "arn:aws:iam::aws:policy/SecretsManagerReadWrite",
# ]

# protocol = "HTTP"
protocol = "HTTPS"

# port = 80
port = 443

certificate_arn = [
  # api.internal.uat.aibots.gov.sg
  "arn:aws:acm:ap-southeast-1:590183886887:certificate/70051f4b-e9b3-4e94-b68f-51d93a1a435d",
  # api.uat.aibots.gov.sg
  "arn:aws:acm:ap-southeast-1:590183886887:certificate/7f954c78-a862-4982-81d1-a7c63bea51de"
]

filter_pattern = "?\"[NOTIFY]\" ?\"[ERROR]\" ?\"caught SIGTERM, shutting down\""

secret_rotation_schedule_expression = "cron( 0 20 * * ? * )" # everyday at 4am

retention_in_days = 365