output inbound{
  value = resource.aws_network_acl_rule.inbound
}

output outbound{
  value = resource.aws_network_acl_rule.outbound
}
