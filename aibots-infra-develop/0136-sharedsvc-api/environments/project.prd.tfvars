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
    "fqdn" : "email.internal.aibots.gov.sg"
    "arn"  : "arn:aws:acm:ap-southeast-1:637423424370:certificate/37abce7c-c2e0-4e3f-958f-a990f5298551"
  }
]

lb_listener_rule_priority = 0