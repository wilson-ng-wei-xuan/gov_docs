# update your project specific environmental 

cpu = 256

memory = 1024 # 512

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
  # uat.aibots.gov.sg
  "arn:aws:acm:ap-southeast-1:590183886887:certificate/820fc00f-ab0c-4977-8668-6e8b2e891481"
]

filter_pattern = "?\"[NOTIFY]\" ?\"[ERROR]\" ?\"caught SIGTERM, shutting down\""

secret_rotation_schedule_expression = "cron( 0 20 * * ? * )" # everyday at 4am

retention_in_days = 365