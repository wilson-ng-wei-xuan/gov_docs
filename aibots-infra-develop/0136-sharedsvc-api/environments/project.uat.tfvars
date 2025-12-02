# update your project specific environmental 

pte_api = [
  {
    name = "email-send"
    host = "email."
    path_pattern = ["/send"]
    retention_in_days = 365
  },
#   {
#     name = "email-parse"
#     host = "email."
#     path_pattern = ["/parse"]
#     retention_in_days = 365
#   },
#   {
#     name = "s3-zipfiles"
#     host = "s3."
#     path_pattern = ["/zipfiles"]
#     retention_in_days = 365
#   },
]

# certificate_arn = []
certificate_arn = [
  {
    "fqdn" : "email.internal.uat.aibots.gov.sg"
    "arn"  : "arn:aws:acm:ap-southeast-1:590183886887:certificate/7d42588e-23c0-4dd6-a736-98f06181a172"
  }
]

lb_listener_rule_priority = 0