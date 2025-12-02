output "lb" {
  value       = aws_lb.simple_lb
  description = <<-EOT
    The Application Load Balancer that is created.
    Read more: [aws_lb](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb)
  EOT
}

output "listener_port_80" {
  # value       = aws_lb_listener.alb_listener_port_80
  value       = var.load_balancer_type == "application" ? aws_lb_listener.alb_listener_port_80 : null
  description = <<-EOT
    The Listener resource for port 80.
    Read more: [lb_listener](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener)
  EOT
}

output "listener_port_443" {
  value       = length( var.certificate_arn ) > 0 && var.load_balancer_type == "application" ? aws_lb_listener.alb_listener_port_443[0] : null
  description = <<-EOT
    The Listener resource for port 443.
    Read more: [lb_listener](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener)
  EOT
}

output "security_group" {
  value       = var.security_group_ids != null ? aws_security_group.for_alb : null
  description = "The security group that is created for the ALB. Only created if security_group_ids is not set."
}

output "aws_s3_bucket_for_access_logs" {
  value       = var.access_logs == null ? module.access_logs_s3_bucket[0] : null
  description = <<-EOT
    The S3 bucket that is created for the ALB access logs. Only created if access_logs is not set.
    Read more: [aws_s3_bucket](https://sgts.gitlab-dedicated.com/wog/gvt/svc-iac/govtech-svc/svc-iac/layer-1-sg/components/aws/s3/simple-s3-private-bucket)
  EOT
}
