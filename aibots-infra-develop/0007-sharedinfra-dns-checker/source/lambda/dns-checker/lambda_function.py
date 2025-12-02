import json
import base64
import boto3
import os
import io
from io import BytesIO
import zipfile

import urllib.parse
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from datetime import datetime, timedelta

import logging
logging.getLogger().setLevel(logging.INFO)

scheduler_client = boto3.client('scheduler') # to add schedule
s3_client = boto3.client("s3") # to read and put files into s3

def lambda_handler(event, context):
  global function_name
  function_name = context.function_name

  Target_Arn =  os.environ['LAMBDA_ARN'] + function_name
  Target_RoleArn = os.environ['EVENT_ROLE_ARN']

  logging.info('got event {}'.format( json.dumps(event) ))

  # ##############################################################################
  # # Triggers by Scheduler
  # ##############################################################################
  # if event.get('source', 'looking for aws.scheduler') == 'aws.scheduler':
  #   logging.info('scheduler activated.' )
  #   return
  for record in event['Records']:
    ############################################################################
    # Triggers by s3
    ############################################################################
    eventSource = ''
    if record.get('eventSource', 'looking for aws:s3') == 'aws:s3':
      eventSource = 's3'
    else:
      eventSource = 'scheduler'

    ############################################################################
    # Get the bucket and json_key value
    ############################################################################
    try:
      logging.info('getting s3 values' )
      bucket = record['s3']['bucket']['name']
      json_key = urllib.parse.unquote_plus( record['s3']['object']['key'] )
      
      base_folder = json_key.replace('.json', '')

    except Exception as e:
      logging.error( '{} >> error missing s3 values >> {}'.format( context.function_name, str(e) ) ) # sends to the channel
      return

    ############################################################################
    # Read the json file
    ############################################################################
    try:
      config = read_file_in_s3( bucket, json_key )

      # try to load as a JSON
      config = json.loads( config )

    except Exception as e:
      logging.error( '{} >> error parsing config >> {}'.format( context.function_name, str(e) ) ) # sends to the channel
      return

    ############################################################################
    # Process the schedules if exist
    ############################################################################
    try:
      schedules = config.get('schedules', {})

      if eventSource == 'scheduler':
        logging.info('{} >> scheduler triggered.'.format( context.function_name ) )

      elif schedules == {}:
        # schedules not in json, to test the DNS 
        logging.info( '{} >> schedules not in config, going to test the DNS.'.format( context.function_name ) )

      elif schedules != {} and eventSource == 's3':
        logging.info('s3 triggered.' )

        schedule_name = context.function_name +'-' +base_folder.replace(' ','_')

        try:
          logging.info( 'Attempting to delete the schedule.' )
          response = scheduler_client.delete_schedule(
            Name = schedule_name
          )
        except Exception as e:
          if 'Schedule ' +schedule_name +' does not exist.' not in str(e):
            logging.error( '{} >> error deleting the schedule >> {}'.format( context.function_name, str(e) ) ) # sends to the channel
            return

        logging.info( 'Attempting to create the schedule.' )
        response = scheduler_client.create_schedule(
          # ActionAfterCompletion = 'DELETE', # this is only for 1 time schedule
          Description = 'Schedules created by bucket >> ' +bucket +' and file >> ' +json_key,
          FlexibleTimeWindow = { "Mode": "OFF" },
          Name = schedule_name,
          ScheduleExpression = schedules['ScheduleExpression'],
          ScheduleExpressionTimezone = schedules.get( 'ScheduleExpressionTimezone', 'Asia/Singapore'),
          State = schedules['State'],
          Target = {
            "Arn": Target_Arn,
            "RoleArn": Target_RoleArn,
            "RetryPolicy": {
              "MaximumEventAgeInSeconds": 60,
              "MaximumRetryAttempts": 0
            },
            "Input": json.dumps( {
              "Records": [
                {
                  "s3": {
                    "bucket": { "name": bucket },
                    "object": { "key": json_key }
                  }
                }
              ]
            } )
          }
        )
        print( response )
        return # there is a schedule, so just add the schedule and exit.

      else:
        # schedules not in json, to test the DNS 
        logging.warn( '{} >> condition not matched, going to test the DNS'.format( context.function_name ) ) # sends to the channel

    except Exception as e:
      logging.info( '{} >> schedules error >> {}'.format( context.function_name, str(e) ) )
      logging.info( '{} >> going to test the DNS'.format( context.function_name ) ) # sends to the channel

    ############################################################################
    # wget the dns
    ############################################################################
    src_file_list = []
    dts = datetime.now()
    dts = dts + timedelta(hours=8)

    dts = dts.strftime("%Y%m%d_%H%M%S")
#    dts = dts['year']+dts['month']+dts['day']+'_'+dts['hour']+dts['minute']+dts['second']

    sites = list( set( config['dns'] ) )

    for site in sites:
      if wget( site ) == 'timed out':
        logging.error('{} is hanging, remove asap.'.format(site) )

    # zip_files_in_s3( bucket, src_file_list, bucket, 'graphs/' +base_folder +'_' +dts +'.zip' )
    # clean_up( bucket, src_file_list )
    # THIS SECTION IS TO PLOT THE GRAPH

################################################################################
def read_file_in_s3( bucket, file ):
  logging.info('read_file_in_s3 activated.' )

  try:
    # Get the file inside the S3 Bucket
    s3_response = s3_client.get_object(
        Bucket = bucket,
        Key = file
    )
  
    # Get the Body object in the S3 get_object() response
    s3_object_body = s3_response.get('Body')

    # Read the data in bytes format
    return s3_object_body.read()

  except Exception as e:
    logging.error( '{} >> error read_file_in_s3 >> {}'.format( '', str(e) ) ) # sends to the channel
    logging.info('exception ended.')

    return "Fail to read file."

################################################################################
def clean_up( src_bucket, src_file_list ):
  logging.info('clean_up activated.' )

  try:
    for src_file in src_file_list:
      logging.info( "deleting s3://{}/{}".format(src_bucket.encode(), src_file.encode()) )
      s3_client.delete_object( Bucket=src_bucket, Key=src_file )

  except Exception as e:
    logging.error( '{} >> error clean_up >> {}'.format( '', str(e) ) ) # sends to the channel
    logging.info('exception ended.')

################################################################################
def zip_files_in_s3( src_bucket, src_file_list, dest_bucket, dest_file ):
  logging.info('zip_files_in_s3 activated.' )

  try:
    # response = {} # seems like not in use.
    archive = BytesIO()
  
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zip_archive:
      for src_file in src_file_list:
        with zip_archive.open( src_file.split('/',)[-1], 'w') as tempfile:
          tempfile.write( s3_client.get_object( Bucket=src_bucket, Key=src_file )['Body'].read() )
  
    archive.seek(0)
    s3_client.upload_fileobj(archive, dest_bucket, dest_file)
    archive.close()

    logging.info( 'zip_files_in_s3 create {}.'.format( dest_file ) )
    return True

  except Exception as e:
    logging.error( '{} >> error in zip_files_in_s3 >> {}'.format( '', str(e) ) ) # sends to the channel
    logging.info('exception ended.')
    return False

################################################################################
def wget( site ):

  try:
    with urlopen('https://' +site  +'/', timeout = 10 ) as response:
      logging.info( 'site {} responded with status: {}'.format(site, response.status) )
      return response.read()

  except HTTPError as error:
    logging.info( 'site {} responded with status: {} and reason: {}'.format(site, error.status, error.reason) )
    return 'site {} responded with status: {} and reason: {}'.format(site, error.status, error.reason)

  except URLError as error:
    logging.info( 'site {} responded with status: nil and reason: {}'.format(site, error.reason) )
    if str( error.reason ) == 'timed out':
      return( 'timed out' )
    else:
      return 'site {} responded with status: nil and reason: {}'.format(site, error.reason)

  except TimeoutError:
    logging.info("timed out")
    return( 'timed out' )