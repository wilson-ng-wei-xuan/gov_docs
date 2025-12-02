import json
import gzip
import base64
import boto3
import os

import urllib3 
http = urllib3.PoolManager() 

import logging
logging.getLogger().setLevel(logging.INFO)

ssm_client = boto3.client('ssm')
default_notification_para = os.environ['DEFAULT_NOTIFICATION']
default_notification = json.loads( ssm_client.get_parameter( Name=default_notification_para, WithDecryption=True )['Parameter']['Value'] )

def lambda_handler(event, context):
  logging.info('got event {}'.format( json.dumps(event) ))

  # let's check where is this coming from
  # cloudwatch logs subscription filter
  if event.get("awslogs", False):
    process_awslogs( event )

  # SNS / SQS
  elif event.get("Records", False):
    # SNS
    if event["Records"][0].get("EventSource", "unknown") == "aws:sns":
      process_sns( event )

    # SQS
    elif event["Records"][0].get("eventSource", "unknown") == "aws:sqs":
      process_sqs( event )

    else:
      logging.error('unknown source in records.')
      process_unknown( event )

  # HTTPS
  elif event.get("requestContext", False).get("elb", False):
    process_https( event )

  else:
    logging.error('unknown event.')
    process_unknown( event )

  logging.info('event ended.')


################################################################################
def process_unknown( event ):
  logging.info('process_unknown activated')
  
  resp = send_notification( default_notification['notification_url'], default_notification['notification_channel'], 'unknown events received' )


################################################################################
# This is for HTTPS payload
# the ALB endpoints was removed. Refer to confluence.
################################################################################
def process_https( event ):
  logging.info( 'process_https activated' )
  
  project_notification = json.loads( event['body'] )
  resp = send_notification( project_notification['notification_url'], project_notification['notification_channel'], project_notification['notification_message'] )


################################################################################
# This is for AWS Cloudwatch Alarm
################################################################################
def process_sqs( event ):
  logging.info( 'process_sqs activated' )
  # cloudwatch metric monitoring uses SNS.
  # process_sns is a little complicated.
  # while any other services can also SNS, we will not bother with them as they should use the HTTPS endpoint
  for index, record in enumerate(event['Records'], start=1):
    logging.debug( "Processing record {} of {}".format(index, len( event['Records'] ) ) )
  
    # load the message as JSON into alarm variable
    message = json.loads( record['body'] )
    logging.info('message {}'.format( json.dumps(message) ) )

    # dissecting AlarmName to get project-code
    # alarm-uatezapp-appraiser-main-web
    project_code = record['eventSourceARN'].split(':')[-1]
    project_code = project_code.split('-')[2]
    logging.info('project_code {}'.format( json.dumps(project_code) ) )
    
    project_notification = swap_project_code( project_code )

    resp = send_notification( project_notification['notification_url'], project_notification['notification_channel'], message )


################################################################################
# This is for AWS Cloudwatch Alarm
################################################################################
def process_sns( event ):
  logging.info( 'process_sns activated' )
  # cloudwatch metric monitoring uses SNS.
  # process_sns is a little complicated.
  # while any other services can also SNS, we will not bother with them as they should use the HTTPS endpoint
  for index, record in enumerate(event['Records'], start=1):
    logging.debug( "Processing record {} of {}".format(index, len( event['Records'] ) ) )
  
    # load the message as JSON into alarm variable
    message = json.loads( record['Sns']['Message'] )
    logging.info('message {}'.format( json.dumps(message) ) )

    # dissecting AlarmName to get project-code
    # alarm-uatezapp-appraiser-main-web
    project_code = message['AlarmName'].split('-')[2]
    logging.info('project_code {}'.format( json.dumps(project_code) ) )
    
    project_notification = swap_project_code( project_code )

    resp = send_notification( project_notification['notification_url'], project_notification['notification_channel'], message )


################################################################################
# This is for AWS Cloudwatch logs subscription
################################################################################
def process_awslogs( event ):
  logging.info( 'process_awslogs activated' )

  cw_data = event["awslogs"]["data"]
  compressed_payload = base64.b64decode(cw_data)
  uncompressed_payload = gzip.decompress(compressed_payload)
  awslogs = json.loads(uncompressed_payload)

  logging.info('cloudwatch logs {}'.format( json.dumps(awslogs) ))

  logGroup = awslogs["logGroup"]
  logStream = awslogs["logStream"]

  # dissecting logGroup to get project-code
  # /aws/lambda/lambda-uatezapp-appraiser-batch-reader
  project_code = awslogs["logGroup"].split('/')[-1]
  project_code = project_code.split('-')[2]
  logging.info('project_code {}'.format( json.dumps(project_code) ) )
  
  project_notification = swap_project_code( project_code )

  message = {
    "logGroup" : awslogs["logGroup"],
    "logStream" : awslogs["logStream"],
    "message" : awslogs['logEvents']
  }

  logging.debug('notification_url {}'.format( json.dumps( project_notification['notification_url'] ) ))
  logging.debug('notification_channel {}'.format( json.dumps( project_notification['notification_channel'] ) ))
  logging.debug('message {}'.format( json.dumps( message ) ))

  resp = send_notification( project_notification['notification_url'], project_notification['notification_channel'], message )


################################################################################
def send_notification( url, channel, message ):
  logging.info( 'send_notification activated' )

  #allow handling of json message.
  if isinstance(message, dict):
    logging.info( 'sorting dict message' )
    # sorted the json by the items into a tuple
    # dict() the tuple back into a json
    message = dict( sorted( message.items() ) )
    # dump it into a string with nice 2 indentation for posting
    text = json.dumps( message, indent = 2 )

  elif isinstance(message, str):
    logging.info( 'text message' )
    # We leave string as is.
    text = message

  else:
    text = 'unhandled message: {} of type: {} pass to send_notification.'.format(message, type(message))
    logging.warning( text )
    send_notification( default_notification['notification_url'], default_notification['notification_channel'], text )

    # reset back to original message and just let it go and try.
    text = message

  # the notify payload
  msg = {
    "channel": channel,
    "username": "WEBHOOK_USERNAME",
    "text": text,
    "icon_emoji" : ""
  }

  # encode the notify_payload
  encoded_msg = json.dumps(msg).encode('utf-8')

  try:
    # send the notify notification
    resp = http.request('POST', url, body=encoded_msg)
    logging.debug('status_code: {} after posting to notify url: {} and channel: {}'.format( resp.status, url, channel ))
  
    if resp.status != 200: # and notify <> default_notification:
      logging.info('notify status_code not 200, going to repost using default.')
  
      resp = send_notification( default_notification['notification_url'], default_notification['notification_channel'], text )

  except:
    resp = send_notification( default_notification['notification_url'], default_notification['notification_channel'], text )

  return resp


################################################################################
def swap_project_code( project_code ):
  # trying to get the para for project_code
  project_para = default_notification_para.split('-')
  project_para[2] = project_code
  project_para.pop() # remove the last "-default"
  project_para = '-'.join( project_para )
  logging.info('project_para {}'.format( json.dumps(project_para) ) )

  return json.loads( ssm_client.get_parameter( Name=project_para, WithDecryption=True )['Parameter']['Value'] )