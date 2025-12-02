import json
import boto3
import os

import logging
logging.getLogger().setLevel(logging.INFO)

sqs_client = boto3.client('sqs', region_name='ap-southeast-1')
sqs_queueurl = os.environ['SQS_FANOUT__URL']

s3_client = boto3.client('s3')

def lambda_handler(event, context):
  logging.info('got event {}'.format( json.dumps(event) ))

  s3_filedrop = event['PROJECT__BUCKET'] # sst-s3-uatezapp-appraiser-003031427344-batch-filedrop-nu8gw66zq
  zipped_appr_folder = event['APPRAISER_BATCH_ZIPPED_APPR__PATH'] # zipped_appr/
  zipped_appr_file = event['APPRAISER_BATCH_ZIPPED_APPR__FILE_EXT'] # .zip

  try:
    # get all the keys in the current folder
    response = s3_client.list_objects_v2(
      Bucket = s3_filedrop,
      Prefix = zipped_appr_folder
    )

    Contents = response.get( 'Contents', [] )
    while response['IsTruncated']:
      response = s3_client.list_objects_v2(
        Bucket = s3_filedrop,
        Prefix = zipped_appr_folder,
        ContinuationToken = response['NextContinuationToken']
      )
      Contents += response.get( 'Contents', [] )
  
    if len( Contents ) > 0:
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


  try:
    for idx, record in enumerate( Contents ):

      logging.info('sending record {} of {} to sqs {}'.format( idx+1, len(Contents), sqs_queueurl ) )
      sqs_client.send_message(
        QueueUrl = sqs_queueurl,
        MessageBody= json.dumps( record | {
          'bucket' : s3_filedrop,
          'key' : record['Key']
        }, default = str )
      )

  except Exception as e:
    logging.error( '{} >> error fanning out to sqs >> {}'.format( context.function_name, str(e) ) ) # sends to the channel
    logging.info('event ended with exception, but no need to Raise as the next schedule will run again.')
    return { 
      'message' : 'exception ended.'
    }


  logging.info('event ended.')
  return { 
    'message' : 'event ended.'
  }