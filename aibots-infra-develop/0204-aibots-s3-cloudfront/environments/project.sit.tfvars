# update your project specific environmental
# you need to create the acm in NV for this cloudfront to recognise
acm_certificate_arn = "arn:aws:acm:us-east-1:471112510129:certificate/cc066cfc-3475-4e1b-89e3-79a2972885ea"

secret_rotation_schedule_expression = "cron( 0 20 * * ? * )" # everyday at 4am

retention_in_days = 365