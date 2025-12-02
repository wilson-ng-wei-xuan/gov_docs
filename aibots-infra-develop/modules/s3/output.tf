output "bucket"{
  value = aws_s3_bucket.the_bucket
  description = <<-EOT
    The S3 bucket that is created.
    Read more: [aws_s3_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket)
  EOT
}

output "aws_s3_bucket_server_side_encryption_configuration"{
  value = aws_s3_bucket_server_side_encryption_configuration.sse
  description = <<-EOT
    The S3 bucket server side encryption configuration that is created.
    Read more: [aws_s3_bucket_server_side_encryption_configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_server_side_encryption_configuration)
  EOT
}

output "aws_s3_bucket_versioning"{
  value = aws_s3_bucket_versioning.s3_bucket_versioning
  description = <<-EOT
    The S3 bucket versioning that is created.
    Read more: [aws_s3_bucket_versioning](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_versioning)
  EOT
}

output "aws_s3_bucket_acl"{
  value = aws_s3_bucket_acl.bucket_acl
  description = <<-EOT
    The S3 bucket acl that is created.
    Read more: [aws_s3_bucket_acl](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_acl)
  EOT
}

output "aws_s3_bucket_public_access_block"{
  value = aws_s3_bucket_public_access_block.public_access_block
  description = <<-EOT
    The S3 bucket public access block that is created.
    Read more: [aws_s3_bucket_public_access_block](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_public_access_block)
  EOT
}