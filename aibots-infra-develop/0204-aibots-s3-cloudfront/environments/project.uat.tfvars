# update your project specific environmental
# you need to create the acm in NV for this cloudfront to recognise
acm_certificate_arn = "arn:aws:acm:us-east-1:590183886887:certificate/f5d56e39-9039-4629-8ec8-ac1328aa2d11"

secret_rotation_schedule_expression = "cron( 0 20 * * ? * )" # everyday at 4am

retention_in_days = 365