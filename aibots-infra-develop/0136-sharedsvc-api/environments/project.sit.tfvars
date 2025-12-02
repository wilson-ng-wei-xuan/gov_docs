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
    "fqdn" : "email.internal.sit.aibots.gov.sg"
    "arn"  : "arn:aws:acm:ap-southeast-1:471112510129:certificate/3c544171-c027-46e5-b647-4d8cd1095c61"
  }
]

lb_listener_rule_priority = 0