# update your project specific environmental
# you need to create the acm in NV for this cloudfront to recognise
acm_certificate_arn = "arn:aws:acm:us-east-1:637423424370:certificate/94199490-f74b-4486-a3c7-e340089b038f"

secret_rotation_schedule_expression = "cron( 0 20 1 /3 ? * )" #first of every 3 month at 4am

retention_in_days = 365