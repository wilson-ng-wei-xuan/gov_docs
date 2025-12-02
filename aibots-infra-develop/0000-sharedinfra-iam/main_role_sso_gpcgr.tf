module "iam-sso-gpcgr" {
  source = "../modules/iam-role"

  name        = "${local.role_name}gpcgr"
  description = "Admin role to be assumed (with Great Power Comes Great Responsibility)"

  custom_trust_relationship_arn = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
  condition_mfa                 = false
  condition_external_id         = "4f8ba940-bf21-4877-89c9-3d805145963f"

  # use this command to find out the role id (permission set id)
  # aws iam list-roles | jq -r '.Roles[] | .RoleName,.RoleId' | grep -i -C 1 'agency_assume_local'
  condition_user_ids = [
    "AROAYS2NTOATY4HDOCQJG:goh_yew_lee@tech.gov.sg",
    "AROAYS2NTOATY4HDOCQJG:david_tw_lee@tech.gov.sg",
  ]
  condition_ip_addresses = [
    # SEED IP
    "8.29.230.18/32",
    "8.29.230.19/32",
  ]

  attach_policies = {
    "read-only-access" : "arn:aws:iam::aws:policy/ReadOnlyAccess",
    "view-only-access" : "arn:aws:iam::aws:policy/job-function/ViewOnlyAccess",
    "aws-support" : "arn:aws:iam::aws:policy/AWSSupportAccess"
  }

  managed_policies = {
    misc = jsonencode(
      {
        "Version" : "2012-10-17",
        "Statement" : [
          {
            "Action" : [
              "inspector2:ListAccountPermissions",
              "sts:TagSession",
              "events:List*",
              "events:Describe*",
              "events:Get*",
              "events:Create*",
              "events:Put*",
              "events:Remove*",
              "events:EnableRule",
              "events:DisableRule",
              "events:Delete*",
              "events:TagResource*",
              "events:UntagResource*",
              "access-analyzer:ApplyArchiveRule",
              "access-analyzer:Create*",
              "access-analyzer:DeleteAnalyzer",
              "access-analyzer:DeleteArchiveRule",
              "access-analyzer:Get*",
              "access-analyzer:List*",
              "access-analyzer:TagResource",
              "access-analyzer:UntagResource",
              "access-analyzer:Update*",
              "access-analyzer:ValidatePolicy",
              "scheduler:*"
            ],
            "Effect" : "Allow",
            "Resource" : "*",
            "Sid" : "MISC"
          }
        ]
      }
    )

    # cloudfront: no distribution deletion
    # eks: no cluster deletion
    # lambda: no function url
    services = jsonencode(
      {
        "Version" : "2012-10-17",
        "Statement" : [
          {
            "Action" : [
              "apigateway:DELETE",
              "apigateway:GET",
              "apigateway:PATCH",
              "apigateway:POST",
              "apigateway:PUT",
              "apigateway:AddCertificateToDomain",
              "apigateway:RemoveCertificateFromDomain",
              "apigateway:SetWebACL",
              "apigateway:UpdateRestApiPolicy",
              "cloudfront:AssociateAlias",
              "cloudfront:Create*",
              "cloudfront:DeleteCachePolicy",
              "cloudfront:DeleteCloudFrontOriginAccessIdentity",
              "cloudfront:DeleteFieldLevelEncryptionConfig",
              "cloudfront:DeleteFieldLevelEncryptionProfile",
              "cloudfront:DeleteFunction",
              "cloudfront:DeleteKeyGroup",
              "cloudfront:DeleteMonitoringSubscription",
              "cloudfront:DeleteOriginAccessControl",
              "cloudfront:DeleteOriginRequestPolicy",
              "cloudfront:DeletePublicKey",
              "cloudfront:DeleteRealtimeLogConfig",
              "cloudfront:DeleteResponseHeadersPolicy",
              "cloudfront:DeleteStreamingDistribution",
              "cloudfront:Describe*",
              "cloudfront:Get*",
              "cloudfront:List*",
              "cloudfront:PublishFunction",
              "cloudfront:TagResource",
              "cloudfront:TestFunction",
              "cloudfront:UntagResource",
              "cloudfront:Update*",
              "lambda:AddLayerVersionPermission",
              "lambda:AddPermission",
              "lambda:Create*",
              "lambda:DeleteAlias",
              "lambda:DeleteCodeSigningConfig",
              "lambda:DeleteEventSourceMapping",
              "lambda:DeleteFunction",
              "lambda:DeleteFunctionCodeSigningConfig",
              "lambda:DeleteFunctionConcurrency",
              "lambda:DeleteFunctionEventInvokeConfig",
              "lambda:DeleteProvisionedConcurrencyConfig",
              "lambda:DisableReplication",
              "lambda:EnableReplication",
              "lambda:Get*",
              "lambda:InvokeAsync",
              "lambda:InvokeFunction",
              "lambda:List*",
              "lambda:PublishLayerVersion",
              "lambda:PublishVersion",
              "lambda:PutFunctionCodeSigningConfig",
              "lambda:PutFunctionConcurrency",
              "lambda:PutFunctionEventInvokeConfig",
              "lambda:PutProvisionedConcurrencyConfig",
              "lambda:RemoveLayerVersionPermission",
              "lambda:RemovePermission",
              "lambda:TagResource",
              "lambda:UntagResource",
              "lambda:Update*",

            ],
            "Effect" : "Allow",
            "Resource" : "*",
            "Sid" : "SERVICES"
          }
        ]
      }
    )

    # highlight: no deletion of vault and recovery points
    backup = jsonencode(
      {
        "Version" : "2012-10-17",
        "Statement" : [
          {
            "Action" : [
              "backup:CopyFromBackupVault",
              "backup:CopyIntoBackupVault",
              "backup:Create*",
              "backup:Delete*",
              "backup:Describe*",
              "backup:Get*",
              "backup:List*",
              "backup:DisassociateRecoveryPoint",
              "backup:DisassociateRecoveryPointFromParent",
              "backup:Put*",
              "backup:TagResource",
              "backup:UntagResource",
              "backup:Update*",
              "backup-storage:CommitBackupJob",
              "backup-storage:DescribeBackupJob",
              "backup-storage:Get*",
              "backup-storage:List*",
              "backup-storage:MountCapsule",
              "backup-storage:NotifyObjectComplete",
              "backup-storage:PutChunk",
              "backup-storage:PutObject",
              "backup-storage:StartObject",
              "backup-storage:UpdateObjectComplete"
            ],
            "Effect" : "Allow",
            "Resource" : "*",
            "Sid" : "BACKUP"
          }
        ]
      }
    )

    # highlight: no deletion of bucket/bucket policy
    storage = jsonencode(
      {
        "Version" : "2012-10-17",
        "Statement" : [
          {
            "Action" : [
              "ecr:BatchCheckLayerAvailability",
              "ecr:BatchDeleteImage",
              "ecr:BatchGetImage",
              "ecr:BatchGetRepositoryScanningConfiguration",
              "ecr:BatchImportUpstreamImage",
              "ecr:CompleteLayerUpload",
              "ecr:CreatePullThroughCacheRule",
              "ecr:CreateRepository",
              "ecr:Delete*",
              "ecr:Describe*",
              "ecr:Get*",
              "ecr:InitiateLayerUpload",
              "ecr:ListImages",
              "ecr:ListTagsForResource",
              "ecr:Put*",
              "ecr:ReplicateImage",
              "ecr:SetRepositoryPolicy",
              "ecr:StartImageScan",
              "ecr:StartLifecyclePolicyPreview",
              "ecr:TagResource",
              "ecr:UntagResource",
              "ecr:UploadLayerPart",
              "s3:AbortMultipartUpload",
              "s3:Create*",
              "s3:DeleteAccessPoint",
              "s3:DeleteAccessPointForObjectLambda",
              "s3:DeleteAccessPointPolicy",
              "s3:DeleteAccessPointPolicyForObjectLambda",
              "s3:DeleteJobTagging",
              "s3:DeleteMultiRegionAccessPoint",
              "s3:DeleteObject*",
              "s3:DeleteStorageLensConfiguration",
              "s3:DeleteStorageLensConfigurationTagging",
              "s3:Describe*",
              "s3:Get*",
              "s3:InitiateReplication",
              "s3:List*",
              "s3:ObjectOwnerOverrideToBucketOwner",
              "s3:Put*",
              "s3:Replicate*",
              "s3:RestoreObject",
              "s3:SubmitMultiRegionAccessPointRoutes",
              "s3:Update*"
            ],
            "Effect" : "Allow",
            "Resource" : "*",
            "Sid" : "STORAGE"
          }
        ]
      }
    )

    account = jsonencode(
      {
        "Version" : "2012-10-17",
        "Statement" : [
          {
            "Action" : [
              "iam:Tag*",
              "iam:Untag*",
              "iam:PassRole",
              "iam:List*",
              "iam:Get*",
              "iam:Detach*",
              "iam:Delete*",
              "iam:Create*",
              "iam:Put*",
              "iam:Update*",
              "iam:Add*",
              "iam:Remove*",
              "iam:Attach*",
              "iam:Set*",
              "iam:GenerateCredentialReport",
              "iam:GenerateServiceLastAccessedDetails",
              "iam:ResetServiceSpecificCredential",
              "iam:SimulateCustomPolicy",
              "iam:SimulatePrincipalPolicy",
              "iam:DeactivateMFADevice",
              "ssm:AddTagsToResource",
              "ssm:AssociateOpsItemRelatedItem",
              "ssm:Cancel*",
              "ssm:Create*",
              "ssm:Delete*",
              "ssm:Deregister*",
              "ssm:Describe*",
              "ssm:DisassociateOpsItemRelatedItem",
              "ssm:Get*",
              "ssm:LabelParameterVersion",
              "ssm:List*",
              "ssm:ModifyDocumentPermission",
              "ssm:Put*",
              "ssm:Register*",
              "ssm:RemoveTagsFromResource",
              "ssm:ResumeSession",
              "ssm:SendAutomationSignal",
              "ssm:SendCommand",
              "ssm:Start*",
              "ssm:StopAutomationExecution",
              "ssm:TerminateSession",
              "ssm:UnlabelParameterVersion",
              "ssm:Update*"
            ],
            "Effect" : "Allow",
            "Resource" : "*",
            "Sid" : "IAMSSM"
          },
          {
            "Action" : [
              "cloudwatch:Delete*",
              "cloudwatch:Describe*",
              "cloudwatch:DisableAlarmActions",
              "cloudwatch:DisableInsightRules",
              "cloudwatch:Enable*",
              "cloudwatch:Get*",
              "cloudwatch:Link",
              "cloudwatch:List*",
              "cloudwatch:Put*",
              "cloudwatch:SetAlarmState",
              "cloudwatch:StartMetricStreams",
              "cloudwatch:StopMetricStreams",
              "cloudwatch:TagResource",
              "cloudwatch:UntagResource",
              "cloudtrail:AddTags",
              "cloudtrail:CancelQuery",
              "cloudtrail:Create*",
              "cloudtrail:Delete*",
              "cloudtrail:Describe*",
              "cloudtrail:Get*",
              "cloudtrail:List*",
              "cloudtrail:LookupEvents",
              "cloudtrail:Put*",
              "cloudtrail:RemoveTags",
              "cloudtrail:RestoreEventDataStore",
              "cloudtrail:Start*",
              "cloudtrail:Stop*",
              "cloudtrail:Update*",
              "logs:AssociateKmsKey",
              "logs:CancelExportTask",
              "logs:Create*",
              "logs:Delete*",
              "logs:Describe*",
              "logs:DisassociateKmsKey",
              "logs:FilterLogEvents",
              "logs:Get*",
              "logs:Link",
              "logs:List*",
              "logs:Put*",
              "logs:StartQuery",
              "logs:StopQuery",
              "logs:Tag*",
              "logs:TestMetricFilter",
              "logs:Unmask",
              "logs:Untag*",
              "logs:UpdateLogDelivery"
            ],
            "Effect" : "Allow",
            "Resource" : "*",
            "Sid" : "CLOUDXX"
          }
        ]
      }
    )

    # highlight: no deletion of hosted zone
    network = jsonencode(
      {
        "Version" : "2012-10-17",
        "Statement" : [
          {
            "Action" : [
              "acm:AddTagsToCertificate",
              "acm:DescribeCertificate",
              "acm:Get*",
              "acm:ImportCertificate",
              "acm:List*",
              "acm:PutAccountConfiguration",
              "acm:RemoveTagsFromCertificate",
              "acm:RenewCertificate",
              "acm:RequestCertificate",
              "acm:ResendValidationEmail",
              "acm:UpdateCertificateOptions",
              "acm-pca:GetCertificate",
              "acm-pca:GetCertificateAuthorityCertificate",
              "acm-pca:IssueCertificate",
              "acm-pca:DescribeCertificateAuthority",
              "elasticloadbalancing:Add*",
              "elasticloadbalancing:Create*",
              "elasticloadbalancing:Delete*",
              "elasticloadbalancing:DeregisterTargets",
              "elasticloadbalancing:Describe*",
              "elasticloadbalancing:Modify*",
              "elasticloadbalancing:RegisterTargets",
              "elasticloadbalancing:Remove*",
              "elasticloadbalancing:Set*",
              "route53:ActivateKeySigningKey",
              "route53:AssociateVPCWithHostedZone",
              "route53:ChangeCidrCollection",
              "route53:ChangeResourceRecordSets",
              "route53:ChangeTagsForResource",
              "route53:Create*",
              "route53:DeactivateKeySigningKey",
              "route53:Delete*",
              "route53:DisableHostedZoneDNSSEC",
              "route53:DisassociateVPCFromHostedZone",
              "route53:EnableHostedZoneDNSSEC",
              "route53:Get*",
              "route53:List*",
              "route53:TestDNSAnswer",
              "route53:Update*",
            ],
            "Effect" : "Allow",
            "Resource" : "*",
            "Sid" : "NETWORK"
          }
        ]
      }
    )

    # highlight: no SMS ($$)
    # highlight: no deletion/purge of queue
    sxs = jsonencode(
      {
        "Version" : "2012-10-17",
        "Statement" : [
          {
            "Action" : [
              "ses:CloneReceiptRuleSet",
              "ses:Create*",
              "ses:Delete*",
              "ses:Describe*",
              "ses:Get*",
              "ses:List*",
              "ses:Put*",
              "ses:Send*",
              "ses:ReorderReceiptRuleSet",
              "ses:Set*",
              "ses:Update*",
              "ses:TestRenderTemplate",
              "ses:VerifyDomainDkim",
              "ses:VerifyDomainIdentity",
              "ses:VerifyEmailAddress",
              "ses:VerifyEmailIdentity",
              "ses:BatchGetMetricData",
              "ses:TagResource",
              "ses:TestRenderEmailTemplate",
              "ses:UntagResource",
              "sns:AddPermission",
              "sns:ConfirmSubscription",
              "sns:Create*",
              "sns:Delete*",
              "sns:Get*",
              "sns:List*",
              "sns:Publish",
              "sns:PutDataProtectionPolicy",
              "sns:RemovePermission",
              "sns:SetEndpointAttributes",
              "sns:SetPlatformApplicationAttributes",
              "sns:SetSubscriptionAttributes",
              "sns:SetTopicAttributes",
              "sns:Subscribe",
              "sns:TagResource",
              "sns:Unsubscribe",
              "sns:UntagResource",
              "sqs:AddPermission",
              "sqs:ChangeMessageVisibility",
              "sqs:CreateQueue",
              "sqs:DeleteMessage",
              "sqs:GetQueueAttributes",
              "sqs:GetQueueUrl",
              "sqs:List*",
              "sqs:ReceiveMessage",
              "sqs:RemovePermission",
              "sqs:SendMessage",
              "sqs:SetQueueAttributes",
              "sqs:TagQueue",
              "sqs:UntagQueue"
            ],
            "Effect" : "Allow",
            "Resource" : "*",
            "Sid" : "SXS"
          }
        ]
      }
    )

    # secretsmanager: no secret deletion/ replication
    # kms: no key deletion/disabling
    # wafv2: no webacl deletion
    security = jsonencode(
      {
        "Version" : "2012-10-17",
        "Statement" : [
          {
            "Action" : [
              "guardduty:List*",
              "guardduty:Get*",
              "guardduty:UpdateDetector",
              "kms:Create*",
              "kms:Decrypt",
              "kms:DeleteAlias",
              "kms:Describe*",
              "kms:Enable*",
              "kms:Encrypt",
              "kms:Generate*",
              "kms:Get*",
              "kms:ImportKeyMaterial",
              "kms:List*",
              "kms:PutKeyPolicy",
              "kms:ReEncryptFrom",
              "kms:ReEncryptTo",
              "kms:RetireGrant",
              "kms:RevokeGrant",
              "kms:ScheduleKeyDeletion",
              "kms:Sign",
              "kms:SynchronizeMultiRegionKey",
              "kms:TagResource",
              "kms:UntagResource",
              "kms:Update*",
              "kms:Verify*",
              "secretsmanager:CancelRotateSecret",
              "secretsmanager:CreateSecret",
              "secretsmanager:DeleteResourcePolicy",
              "secretsmanager:DeleteSecret",
              "secretsmanager:DescribeSecret",
              "secretsmanager:Get*",
              "secretsmanager:List*",
              "secretsmanager:Put*",
              "secretsmanager:RestoreSecret",
              "secretsmanager:RotateSecret",
              "secretsmanager:TagResource",
              "secretsmanager:UntagResource",
              "secretsmanager:Update*",
              "secretsmanager:ValidateResourcePolicy",
              "wafv2:AssociateWebACL",
              "wafv2:CheckCapacity",
              "wafv2:CreateIPSet",
              "wafv2:CreateRegexPatternSet",
              "wafv2:CreateRuleGroup",
              "wafv2:CreateWebACL",
              "wafv2:DeleteWebACL",
              "wafv2:DeleteFirewallManagerRuleGroups",
              "wafv2:DeleteIPSet",
              "wafv2:DeleteLoggingConfiguration",
              "wafv2:DeletePermissionPolicy",
              "wafv2:DeleteRegexPatternSet",
              "wafv2:DeleteRuleGroup",
              "wafv2:DescribeManagedRuleGroup",
              "wafv2:DisassociateFirewallManager",
              "wafv2:DisassociateWebACL",
              "wafv2:GenerateMobileSdkReleaseUrl",
              "wafv2:Get*",
              "wafv2:List*",
              "wafv2:PutFirewallManagerRuleGroups",
              "wafv2:PutLoggingConfiguration",
              "wafv2:PutManagedRuleSetVersions",
              "wafv2:PutPermissionPolicy",
              "wafv2:TagResource",
              "wafv2:UntagResource",
              "wafv2:UpdateIPSet",
              "wafv2:UpdateManagedRuleSetVersionExpiryDate",
              "wafv2:UpdateRegexPatternSet",
              "wafv2:UpdateRuleGroup",
              "wafv2:UpdateWebACL",
              "network-firewall:Associate*",
              "network-firewall:Create*",
              "network-firewall:Delete*",
              "network-firewall:Describe*",
              "network-firewall:DisassociateSubnets",
              "network-firewall:List*",
              "network-firewall:PutResourcePolicy",
              "network-firewall:TagResource",
              "network-firewall:UntagResource",
              "network-firewall:Update*"
            ],
            "Effect" : "Allow",
            "Resource" : "*",
            "Sid" : "SECURITY"
          }
        ]
      }
    )

    ec2 = jsonencode(
      {
        "Version" : "2012-10-17",
        "Statement" : [
          {
            "Action" : [
              "autoscaling:AttachInstances",
              "autoscaling:AttachLoadBalancerTargetGroups",
              "autoscaling:AttachLoadBalancers",
              "autoscaling:BatchDeleteScheduledAction",
              "autoscaling:BatchPutScheduledUpdateGroupAction",
              "autoscaling:CancelInstanceRefresh",
              "autoscaling:CompleteLifecycleAction",
              "autoscaling:CreateAutoScalingGroup",
              "autoscaling:CreateLaunchConfiguration",
              "autoscaling:CreateOrUpdateTags",
              "autoscaling:DeleteAutoScalingGroup",
              "autoscaling:DeleteLaunchConfiguration",
              "autoscaling:DeleteLifecycleHook",
              "autoscaling:DeleteNotificationConfiguration",
              "autoscaling:DeletePolicy",
              "autoscaling:DeleteScheduledAction",
              "autoscaling:DeleteTags",
              "autoscaling:DeleteWarmPool",
              "autoscaling:Describe*",
              "autoscaling:DetachInstances",
              "autoscaling:DetachLoadBalancerTargetGroups",
              "autoscaling:DetachLoadBalancers",
              "autoscaling:DisableMetricsCollection",
              "autoscaling:EnableMetricsCollection",
              "autoscaling:ExecutePolicy",
              "autoscaling:GetPredictiveScalingForecast",
              "autoscaling:Put*",
              "autoscaling:RecordLifecycleActionHeartbeat",
              "autoscaling:ResumeProcesses",
              "autoscaling:Set*",
              "autoscaling:StartInstanceRefresh",
              "autoscaling:SuspendProcesses",
              "autoscaling:TerminateInstanceInAutoScalingGroup",
              "autoscaling:UpdateAutoScalingGroup",
              "ec2:AcceptVpcEndpointConnections",
              "ec2:AcceptVpcPeeringConnection",
              "ec2:Allocate*",
              "ec2:ApplySecurityGroupsToClientVpnTargetNetwork",
              "ec2:AssignIpv6Addresses",
              "ec2:AssignPrivateIpAddresses",
              "ec2:Associate*",
              "ec2:Attach*",
              "ec2:AuthorizeClientVpnIngress",
              "ec2:AuthorizeSecurityGroupEgress",
              "ec2:AuthorizeSecurityGroupIngress",
              "ec2:BundleInstance",
              "ec2:ConfirmProductInstance",
              "ec2:Copy*",
              "ec2:Create*",
              "ec2:Delete*",
              "ec2:Deregister*",
              "ec2:Describe*",
              "ec2:Detach*",
              "ec2:Enable*",
              "ec2:Disable*",
              "ec2:Disassociate*",
              "ec2:Export*",
              "ec2:Get*",
              "ec2:Import*",
              "ec2:ListImagesInRecycleBin",
              "ec2:ListSnapshotsInRecycleBin",
              "ec2:Modify*",
              "ec2:MonitorInstances",
              "ec2:MoveAddressToVpc",
              "ec2:PutResourcePolicy",
              "ec2:RebootInstances",
              "ec2:RegisterImage",
              "ec2:RegisterInstanceEventNotificationAttributes",
              "ec2:RejectVpcEndpointConnections",
              "ec2:RejectVpcPeeringConnection",
              "ec2:ReleaseAddress",
              "ec2:ReleaseHosts",
              "ec2:ReleaseIpamPoolAllocation",
              "ec2:Replace*",
              "ec2:ReportInstanceStatus",
              "ec2:RequestSpotFleet",
              "ec2:RequestSpotInstances",
              "ec2:Reset*",
              "ec2:Restore*",
              "ec2:Revoke*",
              "ec2:RunInstances",
              "ec2:RunScheduledInstances",
              "ec2:Search*",
              "ec2:SendSpotInstanceInterruptions",
              "ec2:Start*",
              "ec2:StopInstances",
              "ec2:TerminateClientVpnConnections",
              "ec2:TerminateInstances",
              "ec2:UnassignIpv6Addresses",
              "ec2:UnassignPrivateIpAddresses",
              "ec2:UnmonitorInstances",
              "ec2:UpdateSecurityGroupRuleDescriptionsEgress",
              "ec2:UpdateSecurityGroupRuleDescriptionsIngress"
            ],
            "Effect" : "Allow",
            "Resource" : "*",
            "Sid" : "EC2"
          }
        ]
      }
    )

  }

  tags = merge(
    {
      "Name" = "${local.role_name}gpcgr"
    }, local.tags
  )
}
