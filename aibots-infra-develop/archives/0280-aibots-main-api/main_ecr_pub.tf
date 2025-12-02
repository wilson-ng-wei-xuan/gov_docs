# note that this does not push the docker image into the ECR.
# You will need to manually push the image.
# Recommendation: when you push the image, push 2 times, 1 with version, 1 with latest.
# terraform can just use latest, so that you do not need to keep changing the image_tag
resource "aws_ecr_repository" "project_pub" {
  count = var.pub.host != null ? 1 : 0

  name                 = "${local.ecr_name}-${var.pub.name}"

  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
  }
}

resource "aws_ecr_lifecycle_policy" "project_pub" {
  count = var.pub.host != null ? 1 : 0

  repository = aws_ecr_repository.project_pub[0].name

  policy = <<EOF
{
    "rules": [
        {
            "rulePriority": 1,
            "description": "Expire untagged images older than 14 days",
            "selection": {
                "tagStatus": "untagged",
                "countType": "sinceImagePushed",
                "countUnit": "days",
                "countNumber": 14
            },
            "action": {
                "type": "expire"
            }
        }
    ]
}
EOF
}

