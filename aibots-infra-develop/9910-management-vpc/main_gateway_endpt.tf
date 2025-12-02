# There are only 2 types of FREE gateway endpoints.
# Let's just keep them all here to make things easier.
locals {
  gateway_endpoint_list = ["com.amazonaws.ap-southeast-1.s3"]
}

resource "aws_vpc_endpoint" "gateway_endpoints" {
  count = length(local.gateway_endpoint_list)

  vpc_id       = local.vpc_id
  service_name = local.gateway_endpoint_list[count.index]

  route_table_ids = values(aws_route_table.project).*.id

  tags = merge(
    local.tags,
    { "Name" = "${local.vpce_name}${local.gateway_endpoint_list[count.index]}" }
  )
}