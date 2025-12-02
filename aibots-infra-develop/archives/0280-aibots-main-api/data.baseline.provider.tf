terraform {
#  required_version = ">= 1.0.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      # version = "~> 5.22.0"
    }
  }
}

provider "aws" {
  region = "ap-southeast-1"
}

# provider "aws" {
#   alias  = "singapore"
#   region = "ap-southeast-1"
# }

# these are terraform data source
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity

data "aws_region" "current" {} # ${data.aws_region.current.name}

data "aws_caller_identity" "current" {} # ${data.aws_caller_identity.current.account_id}