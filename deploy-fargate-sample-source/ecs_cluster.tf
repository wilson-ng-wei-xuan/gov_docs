resource "aws_ecs_cluster" "ecs_cluster" {
  name = local.ecs_cluster_name

  setting {
    name  = "containerInsights"
    value = "${terraform.workspace == "prd" ? "enabled" : "disabled" }"
  }
  # setting {
  #   name  = "containerInsights"
  #   value = "enabled"
  # }
  
  tags = merge(
    local.tags,
    {
      "Name" = local.ecs_cluster_name,
    }
  )
}