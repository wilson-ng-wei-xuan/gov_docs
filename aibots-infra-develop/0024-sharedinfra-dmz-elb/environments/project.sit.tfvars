# # update your project specific environmental
# # you need to manually create the cert in AWS CM because it needs external action on ITSM.
# # you are strongly encourage to create a AWS cert and provide the arn here.
# # it will be messy if you try to create the listener later.
# # you should based on the domain in 0014
certificate_arn = [
  # sit.aibots.gov.sg	
  "arn:aws:acm:ap-southeast-1:471112510129:certificate/03e3b53f-2055-4b17-a5b5-1dceb764b3f3",
]