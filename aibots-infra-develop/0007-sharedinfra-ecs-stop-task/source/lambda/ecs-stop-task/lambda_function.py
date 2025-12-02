import json
import boto3

import time

import logging
logging.getLogger().setLevel(logging.INFO)

ecs_client = boto3.client('ecs')
logs_client = boto3.client('logs')

def lambda_handler(event, context):
  logging.info('got event {}'.format( json.dumps(event) ))

  update_service = ecs_client.update_service(
    cluster = event['cluster'],
    service = event['serviceName'],
    forceNewDeployment=True,
  )

  notification_msg = '[NOTIFY] New Image Pushed into ECR for >> cluster: {} >> family: {} >> Task restarting'.format( event['cluster'], event['family']  )

  # Sent the notification message to sharedsvc channel
  print( notification_msg )

  # log message to ecs log group
  # it will send the notification message to respective channel
  timestamp = int(round(time.time() * 1000))
  LOG_GROUP = '/aws/ecs-task/' + event['family']
  LOG_STREAM = context.function_name +'/' + str(timestamp)

  logs_client.create_log_stream(logGroupName=LOG_GROUP, logStreamName=LOG_STREAM)
  response = logs_client.put_log_events(
      logGroupName=LOG_GROUP,
      logStreamName=LOG_STREAM,
      logEvents=[
          {
              'timestamp': timestamp,
              'message': notification_msg
          }
      ]
  )

  logging.info('event ended.')
  return { 
    'message' : 'event ended.'
  }