# update your project specific environmental
################################################################################
# scheduler
# https://docs.aws.amazon.com/lambda/latest/dg/services-cloudwatchevents-expressions.html
################################################################################
# cron(Minutes Hours Day-of-month Month Day-of-week Year)
# One of the day-of-month or day-of-week values must be a question mark (?).
schedule = "cron(0 0 * * ? *)"
# # For a singular value the unit must be singular (for example, rate(1 day)), otherwise plural (for example, rate(5 days)).
# schedule = "rate(6 minutes)" # to avoid race condition, this should be var.timeout + 1minute

################################################################################
# lambda
################################################################################
retention_in_days = 365

timeout = 30