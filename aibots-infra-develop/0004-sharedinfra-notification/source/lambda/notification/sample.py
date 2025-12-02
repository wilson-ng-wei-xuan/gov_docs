alb={
    "requestContext": {
        "elb": {
            "targetGroupArn": "arn:aws:elasticloadbalancing:ap-southeast-1:003031427344:targetgroup/tg-alb-sharedsvc-notification/f5fd4909f4a10142"
        }
    },
    "httpMethod": "POST",
    "path": "/",
    "queryStringParameters": {},
    "headers": {
        "accept-encoding": "identity",
        "content-length": "904",
        "content-type": "application/json",
        "host": "notification.uat.private.data.tech.gov.sg",
        "user-agent": "python-urllib3/1.26.15",
        "x-amzn-trace-id": "Root=1-65262ea1-72577db719bb8c823351cd20",
        "x-forwarded-for": "172.30.2.93",
        "x-forwarded-port": "443",
        "x-forwarded-proto": "https"
    },
    "body": "{\n    \"notification_channel\": \"whitespace-alerts\",\n    \"notification_message\": {\n        \"email\": \"Leon_LIM@tech.gov.sg\",\n        \"email_verified\": \"false\",\n        \"exp\": 1697001239,\n        \"identities\": \"[{\\\"userId\\\":\\\"eFompFcYNkNmN3IE5nOipSAxvKqkMiPu-mjvhdqeTGM\\\",\\\"providerName\\\":\\\"cognito-uatez-sharedinfra-sso\\\",\\\"providerType\\\":\\\"OIDC\\\",\\\"issuer\\\":null,\\\"primary\\\":true,\\\"dateCreated\\\":1694817603157}]\",\n        \"iss\": \"https://cognito-idp.ap-southeast-1.amazonaws.com/ap-southeast-1_lcJOlJdab\",\n        \"name\": \"Leon LIM (GOVTECH)\",\n        \"preferred_username\": \"Leon_LIM@tech.gov.sg\",\n        \"profile\": \"Leon_LIM@tech.gov.sg\",\n        \"sub\": \"a94ad56c-6061-7009-1303-ea91ce556eca\",\n        \"username\": \"cognito-uatez-sharedinfra-sso_efompfcynknmn3ie5noipsaxvkqkmipu-mjvhdqetgm\"\n    },\n    \"notification_url\": \"https://hooks.slack.com/services/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\"\n}",
    "isBase64Encoded": false
}


dlq={
  "Records": [
    {
      "messageId": "adf33e31-e64e-40ac-a600-0efc9854a6f2",
      "receiptHandle": "AQEB1E1+JGmb2XLqU3zMan9bYBMVArOkhiG32lhP3PLtGX411FNfMve3hg9MsQ8Kf4wgJzzGy3u6ZCux3QMLuZaxpiZvd66ye4rso1hqA+0iEzOAb7IiX0/ka1y2irdSOyC+4nDYgukdmM+qzVj/Y5JCbVlwAriu8Cfi+aDF0JIZJt/nsxlZ8+UREnrh7xvRdMNZvG/8twFlcrYzwoONY7hYZwfmrMfHnukzjsPOp2x2JSP8h0CUqLJ71ED9AZP0yTOXe9G0syI6mYIFqKo2+9tzIjPCMqmKnx6xGW9rcbaYHSyzOdhmqjinfwzS1aYB9eS/YISfMQExbKQ3ln/5rPZdL0hNvMsJjxrx2Nmoyppx7vGTXDXBN7Q4+fJqET7bAmEyV72qM0g47+2eUOATsLasJvuAljCzmgDQkew22c0H3TwmoiM1AhtkI27ul/NJx+s4",
      "body": "{\"Student Name\": \"\\u6211\\u662f\\u597d\\u4eba'meh\", \"town\": \"ANG MO KIO\", \"flat_type\": \"3 ROOM\", \"block\": 174, \"street_name\": \"ANG MO KIO AVE 4\", \"storey_range\": \"07 TO 09\", \"floor_area_sqm\": 60, \"flat_model\": \"Improved\", \"lease_commence_date\": 1986, \"resale_price\": 255000, \"bucket\": \"sst-s3-uatezapp-appraiser-003031427344-batch-filedrop-xmercz4mv\", \"context_key\": \"upload/BLANK/leon_lim@tech.gov.sg/20230930_1456/context.json\", \"output\": \"1_\\u6211\\u662f\\u597d\\u4eba'meh\"}",
      "attributes": {
        "DeadLetterQueueSourceArn": "arn:aws:sqs:ap-southeast-1:003031427344:sqs-uatezapp-appraiser-batch-fanout",
        "ApproximateReceiveCount": "3",
        "AWSTraceHeader": "Root=1-65250495-30b227ef4ea882e709192510;Parent=6b522ce06cfce549;Sampled=0;Lineage=926e4e43:0",
        "SentTimestamp": "1696924828536",
        "SenderId": "AROAQBNFP5EIFIMVCRTJL:lambda-uatezapp-appraiser-batch-reader",
        "ApproximateFirstReceiveTimestamp": "1696924828540"
      },
      "messageAttributes": {},
      "md5OfBody": "da2fc8ac149312111597b4c41fb602fc",
      "eventSource": "aws:sqs",
      "eventSourceARN": "arn:aws:sqs:ap-southeast-1:003031427344:sqs-uatezapp-appraiser-batch-fanout-dlq",
      "awsRegion": "ap-southeast-1"
    }
  ]
}


cw_alarm={
  "Records": [
    {
      "EventSource": "aws:sns",
      "EventVersion": "1.0",
      "EventSubscriptionArn": "arn:aws:sns:ap-southeast-1:003031427344:sns-uatezapp-sharedsvc-notification:11a076fc-a122-4a5a-a52a-634538d53b84",
      "Sns": {
        "Type": "Notification",
        "MessageId": "c88796ea-e668-5127-b30c-cb74121e1d51",
        "TopicArn": "arn:aws:sns:ap-southeast-1:003031427344:sns-uatezapp-sharedsvc-notification",
        "Subject": "ALARM: \"alarm-uatezapp-appraiser-main-web\" in Asia Pacific (Singapore)",
        "Message": "{\"AlarmName\":\"alarm-uatezapp-appraiser-main-web\",\"AlarmDescription\":null,\"AWSAccountId\":\"003031427344\",\"AlarmConfigurationUpdatedTimestamp\":\"2023-10-10T06:32:26.277+0000\",\"NewStateValue\":\"ALARM\",\"NewStateReason\":\"Threshold Crossed: 1 out of the last 1 datapoints [2.0 (10/10/23 06:40:00)] was greater than or equal to the threshold (0.0) (minimum 1 datapoint for OK -> ALARM transition).\",\"StateChangeTime\":\"2023-10-10T06:41:58.348+0000\",\"Region\":\"Asia Pacific (Singapore)\",\"AlarmArn\":\"arn:aws:cloudwatch:ap-southeast-1:003031427344:alarm:test\",\"OldStateValue\":\"INSUFFICIENT_DATA\",\"OKActions\":[\"arn:aws:sns:ap-southeast-1:003031427344:sns-uatezapp-sharedsvc-notification\"],\"AlarmActions\":[\"arn:aws:sns:ap-southeast-1:003031427344:sns-uatezapp-sharedsvc-notification\"],\"InsufficientDataActions\":[\"arn:aws:sns:ap-southeast-1:003031427344:sns-uatezapp-sharedsvc-notification\"],\"Trigger\":{\"MetricName\":\"Invocations\",\"Namespace\":\"AWS/Lambda\",\"StatisticType\":\"Statistic\",\"Statistic\":\"SUM\",\"Unit\":null,\"Dimensions\":[{\"value\":\"lambda-uatezapp-sharedsvc-sso-showheader\",\"name\":\"FunctionName\"}],\"Period\":60,\"EvaluationPeriods\":1,\"DatapointsToAlarm\":1,\"ComparisonOperator\":\"GreaterThanOrEqualToThreshold\",\"Threshold\":0.0,\"TreatMissingData\":\"missing\",\"EvaluateLowSampleCountPercentile\":\"\"}}",
        "Timestamp": "2023-10-10T06:41:58.403Z",
        "SignatureVersion": "1",
        "Signature": "MAH/IXLqNZfGR+AJxEc/eSo8q8+8GYLilKX+QJOeFcmDD7sWXwjnHZ0E9WqMqGPGw+YAHO4Zo8I4CblPKEmVRO9tqWYi/t/GzpCriKgxBWwc8HKTVTHUmmhkGhIGxL9DcWygTBBFBYinV6d3QfJMNVNuRaJoUaNdU1M261k+Gw9gMhyFcJ93m0ufFxR2ILRlfhuqa8/lVSeRTEAUjR/iCHJs8uDn4QdFvek1cDroj+eUmwXxyrW8psVIwwRFY0LnIFr3W4nxb9kefPXAFcVZ6w3S3BP26/w+HSvsTl8+YijTY5h7j+w+7Pb6/tj+9z0jNUxWZ6KGOdRARKsLia0Anw==",
        "SigningCertUrl": "https://sns.ap-southeast-1.amazonaws.com/SimpleNotificationService-01d088a6f77103d0fe307c0069e40ed6.pem",
        "UnsubscribeUrl": "https://sns.ap-southeast-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:ap-southeast-1:003031427344:sns-uatezapp-sharedsvc-notification:11a076fc-a122-4a5a-a52a-634538d53b84",
        "MessageAttributes": {}
      }
    }
  ]
}



awslogs_notification = {
  "awslogs": {
    "data": "H4sIAAAAAAAA/6WT227bOBCGX4Ug9sIBrOhA2bII7IWBdXuzJ8TeqyQQRtTYJkyRBIeK1y36Ln2WPtnCcpI6aBfYA3QhgSD/+ebj6CPvkQh2uDl55JL/tNwsm19W6/Xy/YpPuTtaDFzyLBOZyMuiEmXJp9y43fvgBs8lT+FIqYG+7eD5lQwQ8QN4n4D3ATRhSFqIap8EhA7D5fw6BoSeS15khUjzLM2K9P6Hn5eb1XrzCHknEPOqzVssc1Btsc26GooSslLhfM6nnIaWVNA+amffaRMxEJf3/wXnceRZPaGN54iPXHdcclEtivlCzGoxy0RZF9V8MZtV+aKuqmpRiHmdibqoZ/NZVi6KepFlRV0VlRB8yqPukSL0nst8Xs+LXNSLStRi+uKaS36/urv77e6RLYe4d0F/gHMfqxBcWP2pcOxKsqVleF5iTqkhBOzY5Nv9N+y4R8sUGKPtjsU9st+H1mjaM+cxwCXqD8IgGQQr4UiSIkl5facSiIYeuyQ4g6mGfvy4qPsbb/9QL9PErIsMnsGxY9Exj2HrQi/Z+te1fMW1LCC5ISi8QrUkwSfkhrhHoJjkb8HJ0lcE2kPAjp5UQgbUIbEu6q1WowPWooKBkFnHdIc26nhKWiDsmHdGqxMDY9yRRoPXWKDOxx/sJoDCFtSBTXpHkQVUaOMonhmgeCMf7JfPXz6/0wbZA0+fIKQR6PAsqtkOdky69acHPmVGW2RiPmXasucde7CdwXCJOT8ByTtLyH5kY0PNOA6Tm39fqFyMha5Svl/FUqOMRhtv/aX9ybe1DNhdanSb+lPcOytu8zwlHTHxoA6wQ0pbF51yAdOXrK8gM1GOJA143ZzdXXPEIVhGaLa3TQ8HfN0zeZ3kxkKPU3Y4QtjRdzz8L7a6ulzH2+JXgOfxvvySjTJANPEQCLvmxeCUvQW94Z8eP/0FCThKZ2MFAAA="
  }
}
# Sample on what the awslogs decode to
# {
#   "messageType": "DATA_MESSAGE",
#   "owner": "003031427344",
#   "logGroup": "/aws/lambda/lambda-uatezapp-appraiser-batch-reader",
#   "logStream": "2023/10/02/[$LATEST]a1d3ee17b1be41acb2f0d9a24a04ce66",
#   "subscriptionFilters": [
#     "/aws/lambda/lambda-uatezapp-appraiser-batch-reader"
#   ],
#   "logEvents": [
#     {
#       "id": "37826835935034927685571897778236903929565048298002972733",
#       "timestamp": 1696213987393,
#       "message": "[ERROR] AuthorizationErrorException: An error occurred (AuthorizationError) when calling the Publish operation: User: arn:aws:sts::003031427344:assumed-role/iam-role-uatez-appraiser-batch-reader/lambda-uatezapp-appraiser-batch-reader is not authorized to perform: SNS:Publish on resource: arn:aws:sns:ap-southeast-1:003031427344:sns-uatezapp-sharedsvc-slack-notification because no identity-based policy allows the SNS:Publish action\nTraceback (most recent call last):\n  File \"/var/task/lambda_function.py\", line 36, in lambda_handler\n  response = slack_error()\n  File \"/var/task/lambda_function.py\", line 48, in slack_error\n  response = sns_client.publish(\n  File \"/var/lang/lib/python3.11/site-packages/botocore/client.py\", line 534, in _api_call\n  return self._make_api_call(operation_name, kwargs)\n  File \"/var/lang/lib/python3.11/site-packages/botocore/client.py\", line 976, in _make_api_call\n  raise error_class(parsed_response, operation_name)"
#     }
#   ]
# }
