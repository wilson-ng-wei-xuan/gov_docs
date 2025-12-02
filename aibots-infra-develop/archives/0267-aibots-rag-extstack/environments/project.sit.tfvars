# update your project specific environmental
# lambda
retention_in_days = 365

timeout = 60

# sqs
# https://docs.aws.amazon.com/lambda/latest/operatorguide/sqs-retries.html

redrive_policy_maxReceiveCount = 5
# The maxReceiveCount is the number of times a consumer tries receiving a message from a queue without deleting it before being moved to the dead-letter queue.