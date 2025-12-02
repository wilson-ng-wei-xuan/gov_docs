import json
import boto3
import os
import datetime

import logging
logging.getLogger().setLevel(logging.INFO)

aws_id = os.environ['AWS_ID']
project_rag_status__sqs = os.environ['PROJECT_RAG_STATUS__SQS']
project_rag_parse__sqs = os.environ['PROJECT_RAG_PARSE__SQS']

sqs_client = boto3.client('sqs')

rag_flow = os.environ['RAG_FLOW']
rag_flow_component = os.environ['RAG_FLOW_COMPONENT']

def lambda_handler(event, context):
  # TODO implement
  # Everything is in the event
  logging.info('got event {}'.format( json.dumps(event) ))

  # Do what you need to do
  # https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html
  batch_item_failures = []
  sqs_batch_response = {}

  # loop into the SQS payload, can contain up to 10 records.
  for idx, record in enumerate( event['Records'] ):
    logging.info('processing SNS record {} of {}'.format( idx+1, len( event['Records'] ) ) )

    ##########################################################################
    # # processing sqs message
    ##########################################################################
    try:
      message = json.loads( record['body'] )
      logging.info('{}'.format( json.dumps(message ) ))

      bot_id = message["bot_id"]
      doc_id = message["doc_id"]
      action = message["action"]

      processing = message[rag_flow][rag_flow_component]

      # process the SQS message here.
      config = processing["config"] # TODO: To format based on message structure
      result = processing["result"] # TODO: To format based on message structure

      # after processing, add the result for the next flow
      message["rag_parse"]["zip"]["result"] = {
        "from_rag_flow" : rag_flow,
        "from_rag_flow_component" : rag_flow_component
      }

      # SQS to next rag_flow_component
      response = sqs_client.send_message(
        QueueUrl= project_rag_parse__sqs,
        MessageBody=json.dumps( message )
      )

      logging.info( "Successfully process." )
      logging.info( response )

      status = "success"
      reason = "good job."

    except Exception as e:
      # when there is error processing the message
      # log error to send to slack
      logging.error( '{} >> error processing sqs message >> {}'.format( context.function_name, json.dumps( str(e) ) ) ) # sends to the channel
      # inform SQS this message failed to process at the end
      batch_item_failures.append({"itemIdentifier": record['messageId']})
      status = "fail"
      reason = "{}".format( str(e) )

    ##########################################################################
    # # updating the status
    ##########################################################################
    try:
      # call status zip tp update status
      response = sqs_client.send_message(
        QueueUrl= project_rag_status__sqs,
        MessageBody=json.dumps( {
          "bot_id"    : bot_id,
          "doc_id"    : doc_id,
          "action"    : action,
          "rag_status": {
            "zip" : {
              "flow"      : rag_flow,
              "component" : rag_flow_component,
              "dts"       : datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
              "status"    : status,
              "reason"    : reason
            }
          }
        } )
      )

      logging.info( "Successfully update status." )
      logging.info( response )

    except Exception as e:
      # log error to send to slack
      logging.error('fail to update status with >> {} having error >> {}'.format( project_rag_status__sqs, json.dumps( str(e) ) ) )
      # inform SQS this message failed to process at the end
      batch_item_failures.append( { "itemIdentifier": record['messageId'] } )
      continue # to next record

    ##########################################################################

  # This return will tell SQS to retry which failed message.
  # default all pass will return { "batchItemFailures": [] }
  sqs_batch_response["batchItemFailures"] = batch_item_failures
  logging.info("returning >> ")
  logging.info(sqs_batch_response)

  return sqs_batch_response
  # return {
  #   'statusCode': 200,
  #   'body': results,
  #   'headers': {
  #     'Content-Type': 'application/json',
  #   }
  # }