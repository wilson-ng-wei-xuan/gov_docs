variable "name" {
  description = "(mandatory) name of the role in aws console"
  type        = string
}

variable "description" {
  description = "(mandatory) description of the role"
  type        = string
}

variable "max_session_duration" {
  description = "maximum duration in seconds for role, between 1 to 12 hours"
  type        = number
  default     = 3600
}

variable "path" {
  description = "path of the role in aws console"
  type        = string
  default     = "/"
}

variable "trust_action" {
  description = "the default action in the trusted entity"
  type        = string
  default     = "sts:AssumeRole"
}

variable "principal_type" {
  description = "Principal Type, e.g. `AWS`, `Service`, `Federated`, default to `AWS`."
  type        = string
  default     = "AWS"
  validation {
    condition     = contains(["AWS", "Service", "Federated"], var.principal_type)
    error_message = "Must be one of the options: `AWS`, `Service`, `Federated`."
  }
}

variable "force_detach_policies" {
  description = "force detach policies before destroying the role, default to true"
  type        = bool
  default     = true
}

variable "custom_policy" {
  description = "custom policy to be applied to role using the EOF syntax"
  type        = string
  default     = ""
}

variable "custom_policy_name" {
  description = "Name of the custom policy, default to `custom_policy`"
  type        = string
  default     = "custom_policy"
}

variable "managed_policies" {
  description = "Custom polices to be created managed policies (not inline)."
  type        = map(string)
  default     = {}
}

variable "attach_policies" {
  description = "map(string) of existing policies to attach"
  type        = map(string)
  default     = {}
}

variable "custom_trust_relationship_arn" {
  description = "custom trust relationship, default to :root of the requestor's account, expects a set(string)."
  type        = set(string)
  default     = []
}

variable "condition_account_equal" {
  description = "Determine to add StringEquals: { aws:SourceAccount: xxxx }."
  type        = string
  default     = ""
}

variable "condition_arn_like" {
  description = "Determine to add ArnLike: { aws:SourceArn: xxxx }. Note that not using StringLikes (see https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_condition_operators.html#Conditions_ARN)"
  type        = set(string)
  default     = []
}

variable "condition_user_ids" {
  description = "Determine to add StringLike: { aws:userid: xxxx }, this is used for assumerole in console/ui via federated login."
  type        = set(string)
  default     = []
}

variable "condition_mfa" {
  description = "Determine if MFA will be required when role is asasumed. Default to true, set to false for role chaining."
  type        = bool
  default     = true
}

variable "condition_external_id" {
  description = "External ID to protect role chaining, optional for other cases. Length to be greater than or equalt to 12 characters."
  type        = string
  default     = ""
}

variable "condition_ip_addresses_via_vpce" {
  description = "Only allow role chaining coming from specific IP which goes through vpc endpoint, this rule is disabled if the list is empty. (reference: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-vpcsourceip)"
  type        = list(string)
  default     = []
}

variable "condition_ip_addresses" {
  description = "Only allow role chaining coming from specific IP, this rule is disabled if the list is empty."
  type        = list(string)
  default     = []
}

variable "identity_provider" {
  description = "Web identity provider for federated principle"
  type        = string
  default     = ""
}

variable "condition_identity_providers" {
  description = "Only allow role for the specified identity provider where the object should contain the 'sub' and/or 'aud'"
  type = map(
    object({
      claim_key   = string
      claim_value = string
      test        = string
    })
  )

  validation {
    condition = (
      length(var.condition_identity_providers) == 0 || (
        length(var.condition_identity_providers) == 2 &&
        contains(keys(var.condition_identity_providers), "aud") &&
        contains(keys(var.condition_identity_providers), "sub")
      )
    )
    error_message = "The map must include exactly two objects, one with the 'aud' key and one with the 'sub' key."

  }

  default = {}
}

variable "instance_profile" {
  description = "create instance profile? default: false"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags passed down from parent(s)."
  type        = map(string)
  default     = {}
}
