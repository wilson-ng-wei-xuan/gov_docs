# # update your project specific environmental
# # you need to manually create the cert in AWS CM because it needs external action on ITSM.
# # you are strongly encourage to create a AWS cert and provide the arn here.
# # it will be messy if you try to create the listener later.
# # you should based on the domain in 0014
certificate_arn = [
  # aibots.gov.sg
  "arn:aws:acm:ap-southeast-1:637423424370:certificate/90ac6448-a3d0-4563-91be-65ce1c0ef468",
]