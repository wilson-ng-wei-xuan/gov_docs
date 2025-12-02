########################################################################
########################################################################
# This section has the WAF configuration informations
########################################################################
########################################################################
locals {
  # The list of AWS Managed Rules recommended by Yat Kee
  Managed_Rule_Groups = [
    {
      name = "AWSManagedRulesCommonRuleSet",
      vendor_name = "AWS",
      count_override_name = [
        "SizeRestrictions_BODY", # LLM and upload contains large payload
        "CrossSiteScripting_BODY", # blocking file uploads during testing, so we disabled it
        # "NoUserAgent_HEADER", # blocking cognito
      ]
    },
    {
      name = "AWSManagedRulesAdminProtectionRuleSet",
      vendor_name = "AWS",
      count_override_name = []
    },
    {
      name = "AWSManagedRulesKnownBadInputsRuleSet",
      vendor_name = "AWS",
      count_override_name = []
    },
  ]

  # The list of products we have
  products_regional = [
    {
      content_type          = "TEXT_HTML"
      positional_constraint = "EXACTLY"
      search_string         = local.PUB_URL
      deny_page             = "aibots_deny.html"
      ip_set_arn            = aws_wafv2_ip_set.aibots_ips_regional.arn
    },
  ]

  # products_cloudfront_signed << this has signed_url restriction, match header + Cookies
  # products_cloudfront_public << does NOT have restriction, match header + path
  products_cloudfront_signed = [
    {
      content_type          = "TEXT_HTML"
      positional_constraint = "EXACTLY"
      search_string         = "public.${local.PUB_URL}"
      deny_page             = "403_forbidden_access_by_host.html"
      ip_set_arn            = aws_wafv2_ip_set.aibots_ips_cloudfront.arn
    },
  ]

  products_cloudfront_public = [
    {
      content_type          = "TEXT_HTML"
      positional_constraint = "EXACTLY"
      search_string         = "public.${local.PUB_URL}"
      deny_page             = "403_forbidden_access_by_host.html"
      ip_set_arn            = aws_wafv2_ip_set.whitelisted_ips_cloudfront.arn
    },
  ]
}