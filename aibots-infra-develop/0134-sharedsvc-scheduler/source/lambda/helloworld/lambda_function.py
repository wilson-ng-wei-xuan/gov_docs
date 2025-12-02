import json
import boto3
import os

import logging
logging.getLogger().setLevel(logging.INFO)

sqs_client = boto3.client('sqs', region_name='ap-southeast-1')
s3_client = boto3.client('s3')

def lambda_handler(event, context):
  logging.info('got event {}'.format( json.dumps(event) ))

  schedule_s3 = event['SCHEDULE__BUCKET']
  schedule_path = event['SCHEDULE__PATH'] # zipped_appr/

  try:
    # get all the keys in the folder
    response = s3_client.list_objects_v2(
      Bucket = schedule_s3,
      Prefix = schedule_path
    )

    Contents = response.get( 'Contents', [] )
    while response['IsTruncated']:
      response = s3_client.list_objects_v2(
        Bucket = schedule_s3,
        Prefix = schedule_path,
        ContinuationToken = response['NextContinuationToken']
      )
      Contents += response.get( 'Contents', [] )

    if len( Contents ):
      # Sort the list of dictionaries by the LastModified value
      Contents = sorted(Contents, key=lambda x: x['LastModified'])
    else:
      logging.info('No files to process.')
      return {
        'message' : 'event ended.'
      }
  
  except Exception as e:
    logging.error( '{} >> error collecting bucket contents >> {}'.format( context.function_name, str(e) ) ) # sends to the channel
    logging.info('event ended with exception, but no need to Raise as the next schedule will run again.')
    return { 
      'message' : 'exception ended.'
    }

  # process the content of all the job file
  for file in Contents:
    try:
      logging.info('getting s3://{}/{}'.format( schedule_s3.encode(), file['Key'].encode() ) )
      response = s3_client.get_object( Bucket=schedule_s3, Key=file["Key"] )
      job_json = json.loads( response['Body'].read().decode('utf-8') )

      logging.info('processing s3://{}/{}'.format( schedule_s3.encode(), file['Key'].encode() ) )
      job_json['payload']['schedule'] = {
        "SCHEDULE__BUCKET": schedule_s3,
        "SCHEDULE__PATH": file["Key"]
      }

      logging.info('sending sqs {}'.format( job_json['sqs'].encode() ) )
      response = sqs_client.send_message(
        QueueUrl= job_json['sqs'],
        MessageBody=json.dumps( job_json['payload'] )
      )

    except Exception as e:
      logging.error( '{} >> error processing file {}'.format( context.function_name, 's3://' +schedule_s3 +'/' +file["Key"] ) ) # sends to the channel
      logging.error( '{}'.format( str(e) ) ) # sends to the channel

  # all done.
  return {
    'message' : 'event ended.'
  }