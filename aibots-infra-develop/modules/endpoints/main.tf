resource "aws_vpc_endpoint" "interface_endpt" {
  for_each = {
    for entry in var.interface_endpt: "${entry.service_name}" => entry
  }

  service_name      = each.value["service_name"]
  vpc_endpoint_type = "Interface"

  vpc_id            = var.vpc_id
  subnet_ids = var.subnet_ids
  security_group_ids = var.security_group_ids

  private_dns_enabled = try( each.value["private_dns_enabled"] , false)  

  tags = merge(
    # { "Name" = "${local.vpce_name}-${try( each.value["name"] , each.value["service_name"] ) }" },
    { "Name" = each.value["name"] == null ? "${local.vpce_name}-${each.value["service_name"]}" : "${local.vpce_name}-${each.value["name"]}" },
    local.tags,
    var.additional_tags
  )
}

resource "aws_vpc_endpoint_policy" "interface_endpt" {
  for_each = {
    for entry in var.interface_endpt: "${entry.service_name}" => entry
    if entry.restrict_oubound == true # false if you are doing endpoint sharing, and you need all the route53
    # if entry.private_dns_enabled == false # false if you are doing endpoint sharing, and you need all the route53
  }

  vpc_endpoint_id = aws_vpc_endpoint.interface_endpt[ each.value.service_name ].id
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid": "Allow-Account-Resources",
        "Effect" : "Allow",
        "Principal" : "*",
        "Action": "*",
        "Resource" : "*",
        "Condition": {
          "StringEquals": {
            "aws:ResourceAccount": [
              data.aws_caller_identity.current.account_id
            ]
          }
        }
      }
    ]
  })
}

resource "aws_route53_zone" "interface_endpt" {
  for_each = {
    for entry in aws_vpc_endpoint.interface_endpt: "${entry.service_name}" => entry
    if entry.private_dns_enabled == false # false if you are doing endpoint sharing, and you need all the route53
  }

    name = join( ".", reverse( split( ".", each.value.service_name ) ) )
  
    vpc {
      vpc_id =   var.vpc_id
    }
  
    lifecycle {
      ignore_changes = [ vpc ]
    }
  
    tags = merge(
      local.tags,
      var.additional_tags
    )
}

resource "aws_route53_record" "interface_endpt" {
  for_each = {
    for entry in aws_route53_zone.interface_endpt: "${entry.name}" => entry
  }
    
  zone_id = each.value.id
  name    = each.value.name
  type    = "A"

  alias {
    name                   = aws_vpc_endpoint.interface_endpt[ join( ".", reverse( split( ".", each.value.name ) ) ) ].dns_entry[0].dns_name
    zone_id                = aws_vpc_endpoint.interface_endpt[ join( ".", reverse( split( ".", each.value.name ) ) ) ].dns_entry[0].hosted_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "interface_endpt_wildcard" {
  for_each = {
    for entry in aws_route53_zone.interface_endpt: "${entry.name}" => entry
  }
    
  zone_id = each.value.id
  name    = "*.${each.value.name}"
  type    = "A"

  alias {
    name                   = aws_vpc_endpoint.interface_endpt[ join( ".", reverse( split( ".", each.value.name ) ) ) ].dns_entry[0].dns_name
    zone_id                = aws_vpc_endpoint.interface_endpt[ join( ".", reverse( split( ".", each.value.name ) ) ) ].dns_entry[0].hosted_zone_id
    evaluate_target_health = true
  }
}