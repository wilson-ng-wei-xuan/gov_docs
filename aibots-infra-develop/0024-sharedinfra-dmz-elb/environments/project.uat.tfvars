# # update your project specific environmental
# # you need to manually create the cert in AWS CM because it needs external action on ITSM.
# # you are strongly encourage to create a AWS cert and provide the arn here.
# # it will be messy if you try to create the listener later.
# # you should based on the domain in 0014
certificate_arn = [
  # uat.aibots.gov.sg
  "arn:aws:acm:ap-southeast-1:590183886887:certificate/820fc00f-ab0c-4977-8668-6e8b2e891481",
]