terraform {
  backend "s3" {
    bucket     = "sst-s3-gvt-dsaid-terraform-statefile"
    region     = "ap-southeast-1"
    encrypt    = true
  }
}