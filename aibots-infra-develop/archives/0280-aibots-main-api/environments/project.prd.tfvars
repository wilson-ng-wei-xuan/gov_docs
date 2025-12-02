# update your project specific environmental 

cpu = 256

memory = 512

desired_count = 0 # will set the value to min_capacity
min_capacity = 2
max_capacity = 20

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
  # api.internal.aibots.gov.sg
  "arn:aws:acm:ap-southeast-1:637423424370:certificate/f34be482-62e2-42ca-9597-2c6a6f4a028b",
  # api.aibots.gov.sg
  "arn:aws:acm:ap-southeast-1:637423424370:certificate/78569ad7-c9c1-4964-a476-ddae160c84a1"
]

# filter_pattern = "?\"[NOTIFY]\" ?\"level\\\": \\\"error\" ?\"caught SIGTERM, shutting down\""
filter_pattern = "?\"[NOTIFY]\" ?\"[ERROR]\" ?\"caught SIGTERM, shutting down\""

secret_rotation_schedule_expression = "cron( 0 20 1 /3 ? * )" #first of every 3 month at 4am

retention_in_days = 365