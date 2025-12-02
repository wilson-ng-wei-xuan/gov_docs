variable "route_table_id" {
  type        = list
  description = <<EOF
    The list of route table id that you are making changes.
  EOF
}

variable "transit_gateway_id" {
  type        = string
  description = <<EOF
    The TGW id if you need to route through TGW
  EOF
  default     = null
}

variable "tgw_destination_cidr_block" {
  type        = list
  description = <<EOF
    The list of destination cidr blocks that are route through TGW.
    This is required if you provide transit_gateway_id.
  EOF
  default     = null
}

variable "additional_routes" {
  type        = list
  description = <<EOF
    The list of additional routes, e.g.: to igw, nat, vpce
    refer to https://registry.terraform.io/providers/hashicorp/aws/5.7.0/docs/resources/route
    {
      destination_cidr_block  = "0.0.0.0/0"
      gateway_id              = "igw.id"
    },
    {
      destination_cidr_block  = "0.0.0.0/0"
      nat_gateway_id          = "nat.id"
    }
  EOF
  default = []
}
