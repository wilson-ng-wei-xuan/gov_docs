# for action == "deny" && direction == "both"
#   we will only block the from_port and to_port.
#   this is to satisfy the cloudscape 22 and 3389 deny
# any port in inbound/outbound will have the other side allowing the high ports ( 1024 - 65535 )
# any port in both simply means everything goes thru, because I cannot make 1 BOTH rule to become 2 seperate INBOUND OUTBOUND rule.

# However, do note that we have a ALLOW outbound 0.0.0.0/0 443 before the last DENY ALL.
# This is because we are using aws gateway endpoints for S3.
# This is a list of public IP to S3, managed by AWS.

resource "aws_network_acl_rule" "inbound" {
  for_each  = { for entry in local.nacl_ruleset: "${entry.network_acl_id}.${entry.action}.${entry.direction}.${entry.from_port}.${entry.to_port}.${entry.cidr_block}" => entry }
    egress          = false
    network_acl_id  = each.value.network_acl_id
    rule_action     = each.value.action
    cidr_block      = each.value.cidr_block
    protocol        = 6
    # from_port       = each.value.direction == "inbound" ? lookup(each.value, "port",   0) : ( each.value.direction == "outbound" ?  1024 :   0 )
    # to_port         = each.value.direction == "inbound" ? lookup(each.value, "port", 10000) : ( each.value.direction == "outbound" ? 65535 : 65535 )
    # from_port       = 0
    # to_port         = 65535
    # from_port       = each.value.from_port
    # to_port         = each.value.to_port
    # # for deny, we just block the specific port
    # from_port       = each.value.direction == "both" && each.value.action == "deny" ? each.value.from_port : each.value.direction == "inbound" ? each.value.from_port : each.value.direction == "outbound" ? 1024  : 0
    # to_port         = each.value.direction == "both" && each.value.action == "deny" ? each.value.to_port   : each.value.direction == "inbound" ? each.value.to_port   : each.value.direction == "outbound" ? 65535 : 65535
    from_port       = each.value.action == "deny" ? each.value.from_port : each.value.direction == "inbound" ? each.value.from_port : each.value.direction == "outbound" ? 1024  : 0
    to_port         = each.value.action == "deny" ? each.value.to_port   : each.value.direction == "inbound" ? each.value.to_port   : each.value.direction == "outbound" ? 65535 : 65535
    icmp_code       = lookup(each.value, "icmp_code", 0)
    icmp_type       = lookup(each.value, "icmp_type", 0)
    ipv6_cidr_block = lookup(each.value, "ipv6_cidr_block", null)
    rule_number     = ( floor( index( local.nacl_ruleset, each.value ) / length(var.nacl_ids) ) + 1 ) * var.multiplier
}

resource "aws_network_acl_rule" "outbound" {
  for_each  = { for entry in local.nacl_ruleset: "${entry.network_acl_id}.${entry.action}.${entry.direction}.${entry.from_port}.${entry.to_port}.${entry.cidr_block}" => entry }
    egress          = true
    network_acl_id  = each.value.network_acl_id
    rule_action     = each.value.action
    cidr_block      = each.value.cidr_block
    protocol        = 6
    # from_port       = each.value.direction == "inbound" ?  1024 : ( each.value.direction == "outbound" ? lookup(each.value, "port",   0) :   0 )
    # to_port         = each.value.direction == "inbound" ? 65535 : ( each.value.direction == "outbound" ? lookup(each.value, "port", 10000) : 65535 )
    # from_port       = 0
    # to_port         = 65535
    # from_port       = each.value.from_port
    # to_port         = each.value.to_port
    # # for deny, we just block the specific port
    # from_port       = each.value.direction == "both" && each.value.action == "deny" ? each.value.from_port : each.value.direction == "outbound" ? each.value.from_port : each.value.direction == "inbound" ? 1024  : 0
    # to_port         = each.value.direction == "both" && each.value.action == "deny" ? each.value.to_port   : each.value.direction == "outbound" ? each.value.to_port   : each.value.direction == "inbound" ? 65535 : 65535
    from_port       = each.value.action == "deny" ? each.value.from_port : each.value.direction == "outbound" ? each.value.from_port : each.value.direction == "inbound" ? 1024  : 0
    to_port         = each.value.action == "deny" ? each.value.to_port   : each.value.direction == "outbound" ? each.value.to_port   : each.value.direction == "inbound" ? 65535 : 65535
    icmp_code       = lookup(each.value, "icmp_code", 0)
    icmp_type       = lookup(each.value, "icmp_type", 0)
    ipv6_cidr_block = lookup(each.value, "ipv6_cidr_block", null)
    rule_number     = ( floor( index( local.nacl_ruleset, each.value ) / length(var.nacl_ids) ) + 1 ) * var.multiplier
}

locals {
  # these are mandatory to specify:
  # "action"
  # "cidr_block"
  # "direction" = "inbound" | "outbound" | "both"

  # protocol is fixed to tcp (6), 
  # "protocol"      = "6"
  # depending on "direction", to_port and from_port range from 0 to 65535
  # "from_port"     = 0
  # "to_port"       = 65535

  # these are optional with default values if you do not specify:
  # "port"          = SEE ABOVE, but you should leave this empty, ports are lock down at security group
  # "icmp_code"     = 0
  # "icmp_type"     = 0
  # "ipv6_cidr_block" = null
  default_deny_vpc = distinct(
    flatten(
      [for index in range( length( var.deny_vpc_cidr ) ) :
        {
          action = "deny"
          direction = "both"
          from_port   = 0
          to_port     = 65535
          cidr_block = var.deny_vpc_cidr[ index ]
        }
      ]
    )
  )

  nacl_rules = var.allow_ssh_rdp ? concat(
      var.nacl_rules,
      local.default_deny_vpc,
      # # allow ALL from AWS services gateway endpoints
      # # if we allow AWS services gateway endpoints 1 by 1 will exceed the limit
      [{
        action      = "allow"
        direction   = "outbound"
        from_port   = 443
        to_port     = 443
        cidr_block  = "0.0.0.0/0"
      }],
    ) : concat(
    [{
      action      = "deny"
      direction   = "both"
      from_port   = 22
      to_port     = 22
      cidr_block  = "0.0.0.0/0"
    },
    {
      action      = "deny"
      direction   = "both"
      from_port   = 3389
      to_port     = 3389
      cidr_block  = "0.0.0.0/0"
    }],
    var.nacl_rules,
    local.default_deny_vpc,
    # # allow ALL 0.0.0.0/0:443 outbound
    # # actual control is at route table, routing traffic to networkfirewall
    # # networkfirewall will whitelist according to the destination FQDN.
    [{
      action      = "allow"
      direction   = "outbound"
      from_port   = 443
      to_port     = 443
      cidr_block  = "0.0.0.0/0"
    }],
  )

  nacl_ruleset = distinct(
    flatten(
      [for rule in local.nacl_rules :
        [for index in range( length( var.nacl_ids ) ) :
          {
            network_acl_id  = var.nacl_ids[ index ]
            action          = rule.action
            direction       = rule.direction
            from_port       = lookup(rule, "from_port", 0)
            to_port         = lookup(rule, "to_port", 65535)
            cidr_block      = rule.cidr_block
          }
        ]
      ]
    )
  )
}
