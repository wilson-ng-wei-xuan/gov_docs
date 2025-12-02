# note that this does not push the docker image into the ECR.
# You will need to manually push the image.
# Recommendation: when you push the image, push 2 times, 1 with version, 1 with latest.
# terraform can just use latest, so that you do not need to keep changing the image_tag

locals {
  # if length > 32, then truncate to 32; Ensure local.names do not throw an error
  ecr_name = substr( "${local.ecr_prefix}-${terraform.workspace}${var.zone}${var.tier}-${var.project_code}${var.project_desc}", 0, 256)
}

resource "aws_ecr_repository" "ecr_repository" {
  name                 = "${local.ecr_name}"

  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
  }
}