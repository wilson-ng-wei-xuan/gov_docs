# note that this does not push the docker image into the ECR.
# You will need to manually push the image.
# Recommendation: when you push the image, push 2 times, 1 with version, 1 with latest.
# terraform can just use latest, so that you do not need to keep changing the image_tag
resource "aws_ecr_repository" "project" {
  for_each  = { for entry in var.process: "${entry.name}" => entry if entry.package_type == "Image" }

  name                 = "${local.ecr_name}-${each.value.name}"

  image_tag_mutability = "MUTABLE"

  force_delete         =true

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
  }
}

resource "aws_ecr_lifecycle_policy" "project" {
  for_each  = { for entry in var.process: "${entry.name}" => entry if entry.package_type == "Image" }

  repository = aws_ecr_repository.project[each.value.name].name

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

################################################################################
# This part onwards is the image
################################################################################
locals {
  # ECR docker registry URI
  ecr_reg   = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.name}.amazonaws.com" 
  
  image_tag = "latest"  # image tag

  dkr_img_src_path = "${path.module}/source/image"
  dkr_img_src_sha256 = sha256(join("", [for f in fileset(".", "${local.dkr_img_src_path}/**") : file(f)]))
  
  build_push_dkr_img = null_resource.build_push_dkr_img[*]
}

variable "force_image_rebuild" {
  type    = bool
  default = false
}

# local-exec for build and push of docker image
resource "null_resource" "build_push_dkr_img" {
  for_each  = { for entry in var.process: "${entry.name}" => entry if entry.package_type == "Image" }

  triggers = {
    detect_docker_source_changes = var.force_image_rebuild == true ? timestamp() : local.dkr_img_src_sha256
  }

  provisioner "local-exec" {
    command = <<-EOT
      aws ecr get-login-password --region ${data.aws_region.current.name} | docker login --username AWS --password-stdin ${local.ecr_reg}

      docker build -t ${local.ecr_reg}/${each.value.name}:${local.image_tag} -f ${local.dkr_img_src_path}/Dockerfile .

      docker tag ${local.ecr_reg}/${each.value.name}:${local.image_tag} ${local.ecr_reg}/${aws_ecr_repository.project[each.value.name].name}:${local.image_tag}

      docker push ${local.ecr_reg}/${aws_ecr_repository.project[each.value.name].name}:${local.image_tag}
    EOT
  }
}

# output "trigged_by" {
#   for_each  = { for entry in var.process: "${entry.name}" => entry if entry.package_type == "Image" }
#   value = null_resource.build_push_dkr_img[each.value.name].triggers
# }