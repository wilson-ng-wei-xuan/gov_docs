# update your project specific environmental 

cpu = 256

memory = 512

desired_count = 0 # will set the value to min_capacity
min_capacity = 1
max_capacity = 2

scale_in_cooldown = 0 # 0 will take 2*var.health_check_grace_period_seconds
scale_out_cooldown = 0 # 0 will take 2*var.health_check_grace_period_seconds

health_check_grace_period_seconds = 60

# task_role_managed_policy_arns = [
#   "arn:aws:iam::aws:policy/AmazonS3FullAccess",
# ]

# protocol = "HTTP"
protocol = "HTTPS"

# port = 80
port = 443

certificate_arn = [
  # sit.aibots.gov.sg
  "arn:aws:acm:ap-southeast-1:471112510129:certificate/03e3b53f-2055-4b17-a5b5-1dceb764b3f3"
]

# filter_pattern = "?\"[NOTIFY]\" ?\"level\\\": \\\"error\" ?\"caught SIGTERM, shutting down\""
filter_pattern = "?\"[NOTIFY]\" ?\"[ERROR]\" ?\"caught SIGTERM, shutting down\""

secret_rotation_schedule_expression = "cron( 0 /4 * * ? * )" # "cron( 0 20 1 * ? * )" # first of every month at 4am

retention_in_days = 365