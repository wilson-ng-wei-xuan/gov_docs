import json
import base64
import boto3
import os
from PIL import Image
import io
from io import BytesIO
import zipfile
import urllib.parse

from datetime import datetime, timedelta

import logging
logging.getLogger().setLevel(logging.INFO)

cw_client = boto3.client("cloudwatch") # to plot graphs
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
      grapher_config = read_file_in_s3( bucket, json_key )

      # try to load as a JSON
      grapher_config = json.loads( grapher_config)
      
      start = grapher_config.get( 'start', '' )
      end = grapher_config.get( 'end', '' )

    except Exception as e:
      logging.error( '{} >> error parsing grapher_config >> {}'.format( context.function_name, str(e) ) ) # sends to the channel
      return

    ############################################################################
    # Process the graph_schedules if exist
    ############################################################################
    try:
      graph_schedules = grapher_config.get('graph_schedules', {})

      if eventSource == 'scheduler':
        logging.info('{} >> scheduler triggered.'.format( context.function_name ) )

      elif graph_schedules == {}:
        # graph_schedules not in json, to plot past 3 hours 
        logging.info( '{} >> graph_schedules not in config, going to plot past 3 hours.'.format( context.function_name ) )

      elif graph_schedules != {} and eventSource == 's3':
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
          ScheduleExpression = graph_schedules['ScheduleExpression'],
          ScheduleExpressionTimezone = graph_schedules.get( 'ScheduleExpressionTimezone', 'Asia/Singapore'),
          State = "ENABLED",
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

        return # there is a schedule, so just add the schedule and exit.

      else:
        # graph_schedules not in json, to plot past 3 hours 
        logging.warn( '{} >> condition not matched, going to plot past 3 hours'.format( context.function_name ) ) # sends to the channel

    except Exception as e:
      logging.info( '{} >> graph_schedules error >> {}'.format( context.function_name, str(e) ) )
      logging.info( '{} >> going to plot past 3 hours'.format( context.function_name ) ) # sends to the channel

    ############################################################################
    # Plotting the graphs
    ############################################################################
    src_file_list = []
    dts = datetime.now()
    dts = dts + timedelta(hours=8)

    dts = dts.strftime("%Y%m%d_%H%M%S")
#    dts = dts['year']+dts['month']+dts['day']+'_'+dts['hour']+dts['minute']+dts['second']

    for chart in grapher_config['graph_charts']:
      # Namespace is a container for CloudWatch MetricNames
      # MetricName represents a time-ordered set of data points that are published to CloudWatch
      # dimension is a name/value pair that is part of the identity of a MetricName.

      # Get all the metrics available witht he Namespace and MetricName
      Namespace = chart['Namespace']
  
      cloudwatch_metrics = []
      for MetricName in chart['MetricName']:
        # print('pulling Namespace>> {} MetricName >> {}'.format(Namespace, MetricName))
        
        response = cw_client.list_metrics(
          Namespace = Namespace,
          MetricName = MetricName
        )
  
        # we are now collecting the Metrics
        # this is to cater to the Multi Metrics plot like Fargate Task count, and Database Queries.
        cloudwatch_metrics.append( response['Metrics'] )
  
      # we will now match those cloudwatch_metrics that matches the graph_filter
      # each set of graph_filter is a graph
      for graph_filter in chart['graphs_filter']:
  
        graph_plot_metrics = [] # graph_plot_metrics is a metric collector to plot a graph, especially multi-az plot
  
        # looping into each matric to discard the unmatch metric_dimension
        for cw_metric in cloudwatch_metrics:
  
          for dimension in cw_metric:
            # doing things the smart/lazy way to just find a match in the coverted string
            dimension_str = json.dumps( dimension )
  
            gf_matcher = [] # a true/false collect to check if the ALL the gf matches
            for gf in graph_filter:
  
              if gf in dimension_str:
                gf_matcher.append( True )
              else:
                gf_matcher.append( False )
  
            if all( gf_matcher ):
              graph_plot_metrics.append( dimension )
              
              # generating the name
              for kv_dimension in dimension['Dimensions']:
                if kv_dimension['Name'] == chart['filename']:
                  filename = dimension['Namespace'] +'-' +dimension['MetricName'] +'-' +kv_dimension['Value']
                  filename = filename.replace('/','_')
                  break
  
        if not graph_plot_metrics:
          logging.info( '{} >> No graph_plot_metrics.'.format( context.function_name ) )
  
        else:
          # convert the graph_plot_metrics into cw_client.get_metric_widget_image compatible
          logging.info( '{} >> Parsing graph_plot_metrics for filename >> {}'.format( context.function_name, filename ) )
          graph_plot_metrics = image_metrics_data_parser( chart['stats'], graph_plot_metrics )
  
    # THIS SECTION IS TO PLOT THE GRAPH
          image = get_cloudwatch_image( graph_plot_metrics,
                                        start, end,
                                        chart['stacked'],
                                        "timeSeries" )
        
          # Save the image to an in-memory file
          img = Image.open(BytesIO( image ))
          buffer = io.BytesIO()
          img.save(buffer,"PNG")
        
          # You need this part, remarked to test below
          # Upload image to s3
          buffer.seek(0)
          s3_client.upload_fileobj(buffer, bucket, base_folder +'/' +filename +'.png')
          
          src_file_list.append( base_folder +'/' +filename +'.png' )
  
    zip_files_in_s3( bucket, src_file_list, bucket, 'graphs/' +base_folder +'_' +dts +'.zip' )
    clean_up( bucket, src_file_list )
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
def image_metrics_data_parser( stats, graph_plot_metrics ):

  data_parser = []
  for graph_plot in graph_plot_metrics:
    image_metric = []
    image_metric.append(graph_plot['Namespace'])
    image_metric.append(graph_plot['MetricName'])

    for dimension in graph_plot['Dimensions']:
      image_metric.append(dimension['Name'])
      image_metric.append(dimension['Value'])

    # 
    for stat in stats:
      working_temp = image_metric.copy()
      working_temp.append( { "stat": stat } )

      data_parser.append( working_temp )

  return data_parser


def get_cloudwatch_image( metrics, start, end, stacked, view ):
  # https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/CloudWatch-Metric-Widget-Structure.html
  response = cw_client.get_metric_widget_image(
    MetricWidget = json.dumps( {
      "title" : "", # str( metrics ), # "This is the title",
      "stacked": stacked,
      "stats" : "", # SampleCount | Average | Sum | Minimum | Maximum | p?? | TM(??:??), TC(??:??) | TS(??:??) | WM(??:??) | PR(??:??) | IQM
      "metrics": metrics, # [
                          #   [ "AWS/ApplicationELB", "ActiveConnectionCount", "TargetGroup", "targetgroup/tg-alb-appraiser-main-web/3975358861358408" ]
                          # ],
      "start"  : start,
      "end"    : end,
      "period" : 60,
      "view" : view, # timeSeries | bar | pie
      "width"  : 1800,
      "height" :  600,
      "legend": { "position" : "bottom" }, # bottom | right | hidden
      "theme" : "light", # light | dark
      "timezone" : "+0800",
      "yAxis" : {
        "left": {
          "min": 0,
          # "max": 100
        },
        "right": {
          "min": 0
        }
      }
    } )
  )

  return( response["MetricWidgetImage"] )