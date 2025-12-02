# configuration are passed in during init with
# -backend-config="./environments/backend.$2.tfvars"
terraform {
  backend "s3" {}
}