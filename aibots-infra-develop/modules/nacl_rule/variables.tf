variable "multiplier" {
  type  = number
  description = <<EOF
    NACL rule multiplier, so that there are gaps inbetween rules to manually add new rules when needed.
  EOF
  default = 10
}

variable "deny_vpc_cidr" {
  type  = list
  description = <<EOF
    A list of cidr_block in the VPCs, this will be use to deny traffic within vpc.
  EOF
  default = []

  validation {
    condition = alltrue([
      for cidr in var.deny_vpc_cidr : can( cidrhost( cidr, 0) )
    ])
    error_message = <<EOF
      deny_vpc_cidr must be valid IPv4 CIDR. "123.123.123.123/32".
    EOF
  }
}

variable "nacl_ids" {
  type        = list
  description = <<EOF
    The list of nacl id that you are making changes.
  EOF
}

variable "nacl_rules" {
  type = list( object({
    action      = string
    direction   = string
    from_port   = number
    to_port     = number
    cidr_block  = string
  }) )

  description = <<EOF
    The list of nacl rules that you are adding, e.g.:
    [
      { 
        action      = "allow" # allow | deny
        direction   = "outbound" # inbound | outbound | both
        from_port   = 443
        to_port     = 443
        cidr_block  = "1.2.3.4/32" # cidr block to allow or deny
      },
    ]
  EOF

  validation {
    condition = alltrue([
      for o in var.nacl_rules : contains(["allow", "deny"], o.action)
    ])
    error_message = <<EOF
      action can only be "allow" or "deny".
    EOF
  }
  validation {
    condition = alltrue([
      for o in var.nacl_rules : contains(["inbound", "outbound", "both"], o.direction)
    ])
    error_message = <<EOF
      direction can only be "inbound", "outbound" or "both".
    EOF
  }
  validation {
    condition = alltrue([
      for o in var.nacl_rules : o.from_port >= 0 && o.from_port <= 65535 && o.from_port <= o.to_port && floor(o.from_port) == o.from_port
    ])
    error_message = <<EOF
      from_port can only be number and <= to_port
    EOF
  }
  validation {
    condition = alltrue([
      for o in var.nacl_rules : o.to_port >= 0 && o.to_port <= 65535 && o.from_port <= o.to_port && floor(o.to_port) == o.to_port
    ])
    error_message = <<EOF
      to_port can only be number and >= from_port
    EOF
  }
  validation {
    condition     = alltrue([
      for o in var.nacl_rules : can( cidrhost( o.cidr_block, 0) )
    ])
    error_message = <<EOF
      cidr_block must be valid IPv4 CIDR."123.123.123.123/32".
    EOF
  }
}

variable "allow_ssh_rdp" {
  type        = bool
  default     = false
  description = <<EOF
    This adds a deny 22 3389 at the very top.
  EOF
}
