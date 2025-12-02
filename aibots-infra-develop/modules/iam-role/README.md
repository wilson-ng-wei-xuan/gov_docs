## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.3 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | 5.40.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.40.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_iam_instance_profile.instance_profile](https://registry.terraform.io/providers/hashicorp/aws/5.40.0/docs/resources/iam_instance_profile) | resource |
| [aws_iam_policy.managed_policies](https://registry.terraform.io/providers/hashicorp/aws/5.40.0/docs/resources/iam_policy) | resource |
| [aws_iam_role.iam_role](https://registry.terraform.io/providers/hashicorp/aws/5.40.0/docs/resources/iam_role) | resource |
| [aws_iam_role_policy.custom_policy](https://registry.terraform.io/providers/hashicorp/aws/5.40.0/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy_attachment.attach_policy](https://registry.terraform.io/providers/hashicorp/aws/5.40.0/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.managed_policies](https://registry.terraform.io/providers/hashicorp/aws/5.40.0/docs/resources/iam_role_policy_attachment) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/5.40.0/docs/data-sources/caller_identity) | data source |
| [aws_iam_policy_document.iam_trusted](https://registry.terraform.io/providers/hashicorp/aws/5.40.0/docs/data-sources/iam_policy_document) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_attach_policies"></a> [attach\_policies](#input\_attach\_policies) | map(string) of existing policies to attach | `map(string)` | `{}` | no |
| <a name="input_condition_account_equal"></a> [condition\_account\_equal](#input\_condition\_account\_equal) | Determine to add StringEquals: { aws:SourceAccount: xxxx }. | `string` | `""` | no |
| <a name="input_condition_arn_like"></a> [condition\_arn\_like](#input\_condition\_arn\_like) | Determine to add ArnLike: { aws:SourceArn: xxxx }. Note that not using StringLikes (see https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_condition_operators.html#Conditions_ARN) | `set(string)` | `[]` | no |
| <a name="input_condition_external_id"></a> [condition\_external\_id](#input\_condition\_external\_id) | External ID to protect role chaining, optional for other cases. Length to be greater than or equalt to 12 characters. | `string` | `""` | no |
| <a name="input_condition_identity_providers"></a> [condition\_identity\_providers](#input\_condition\_identity\_providers) | Only allow role for the specified identity provider where the object should contain the 'sub' and/or 'aud' | <pre>map(<br/>    object({<br/>      claim_key   = string<br/>      claim_value = string<br/>      test        = string<br/>    })<br/>  )</pre> | `{}` | no |
| <a name="input_condition_ip_addresses"></a> [condition\_ip\_addresses](#input\_condition\_ip\_addresses) | Only allow role chaining coming from specific IP, this rule is disabled if the list is empty. | `list(string)` | `[]` | no |
| <a name="input_condition_ip_addresses_via_vpce"></a> [condition\_ip\_addresses\_via\_vpce](#input\_condition\_ip\_addresses\_via\_vpce) | Only allow role chaining coming from specific IP which goes through vpc endpoint, this rule is disabled if the list is empty. (reference: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-vpcsourceip) | `list(string)` | `[]` | no |
| <a name="input_condition_mfa"></a> [condition\_mfa](#input\_condition\_mfa) | Determine if MFA will be required when role is asasumed. Default to true, set to false for role chaining. | `bool` | `true` | no |
| <a name="input_condition_user_ids"></a> [condition\_user\_ids](#input\_condition\_user\_ids) | Determine to add StringLike: { aws:userid: xxxx }, this is used for assumerole in console/ui via federated login. | `set(string)` | `[]` | no |
| <a name="input_custom_policy"></a> [custom\_policy](#input\_custom\_policy) | custom policy to be applied to role using the EOF syntax | `string` | `""` | no |
| <a name="input_custom_policy_name"></a> [custom\_policy\_name](#input\_custom\_policy\_name) | Name of the custom policy, default to `custom_policy` | `string` | `"custom_policy"` | no |
| <a name="input_custom_trust_relationship_arn"></a> [custom\_trust\_relationship\_arn](#input\_custom\_trust\_relationship\_arn) | custom trust relationship, default to :root of the requestor's account, expects a set(string). | `set(string)` | `[]` | no |
| <a name="input_description"></a> [description](#input\_description) | (mandatory) description of the role | `string` | n/a | yes |
| <a name="input_force_detach_policies"></a> [force\_detach\_policies](#input\_force\_detach\_policies) | force detach policies before destroying the role, default to true | `bool` | `true` | no |
| <a name="input_identity_provider"></a> [identity\_provider](#input\_identity\_provider) | Web identity provider for federated principle | `string` | `""` | no |
| <a name="input_instance_profile"></a> [instance\_profile](#input\_instance\_profile) | create instance profile? default: false | `bool` | `false` | no |
| <a name="input_managed_policies"></a> [managed\_policies](#input\_managed\_policies) | Custom polices to be created managed policies (not inline). | `map(string)` | `{}` | no |
| <a name="input_max_session_duration"></a> [max\_session\_duration](#input\_max\_session\_duration) | maximum duration in seconds for role, between 1 to 12 hours | `number` | `3600` | no |
| <a name="input_name"></a> [name](#input\_name) | (mandatory) name of the role in aws console | `string` | n/a | yes |
| <a name="input_path"></a> [path](#input\_path) | path of the role in aws console | `string` | `"/"` | no |
| <a name="input_principal_type"></a> [principal\_type](#input\_principal\_type) | Principal Type, e.g. `AWS`, `Service`, `Federated`, default to `AWS`. | `string` | `"AWS"` | no |
| <a name="input_tags"></a> [tags](#input\_tags) | Tags passed down from parent(s). | `map(string)` | `{}` | no |
| <a name="input_trust_action"></a> [trust\_action](#input\_trust\_action) | the default action in the trusted entity | `string` | `"sts:AssumeRole"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_arn"></a> [arn](#output\_arn) | arn of the role |
| <a name="output_create_date"></a> [create\_date](#output\_create\_date) | date which the role was created |
| <a name="output_description"></a> [description](#output\_description) | description of the role |
| <a name="output_id"></a> [id](#output\_id) | id of the role |
| <a name="output_name"></a> [name](#output\_name) | name of the role |
| <a name="output_role_session_duration"></a> [role\_session\_duration](#output\_role\_session\_duration) | maximum duration a role can be assume for |
| <a name="output_trust_policy"></a> [trust\_policy](#output\_trust\_policy) | trust role policy of this role |
| <a name="output_unique_id"></a> [unique\_id](#output\_unique\_id) | unique id of the role |
