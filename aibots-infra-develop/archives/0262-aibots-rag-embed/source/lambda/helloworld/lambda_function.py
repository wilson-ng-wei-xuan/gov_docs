import json
import boto3
import os
import datetime

import logging
logging.getLogger().setLevel(logging.INFO)

from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

project_rag_opensearch__endpoint = os.environ['PROJECT_RAG_OPENSEARCH__ENDPOINT'].replace("https://","")
project_rag_opensearch__name = os.environ['PROJECT_RAG_OPENSEARCH__NAME']
aws_id = os.environ['AWS_ID']
project_rag_status__sqs = os.environ['PROJECT_RAG_STATUS__SQS']

sqs_client = boto3.client('sqs')

rag_flow = os.environ['RAG_FLOW']
rag_flow_component = os.environ['RAG_FLOW_COMPONENT']

class FileIndexer:
  # CRUD >> CREATE
  def __init__(self, host, index_name):
    """Upload files"""
    # Initialize index
    self.index_name = index_name
    region = 'ap-southeast-1'  
    service = 'aoss'
    credentials = boto3.Session().get_credentials()
    self.auth = AWSV4SignerAuth(credentials, region, service)

    # create an opensearch client and use the request-signer
    self.client = OpenSearch(
      hosts=[{'host': host, 'port': 443}],
      http_auth=self.auth,
      use_ssl=True,
      verify_certs=True,
      connection_class=RequestsHttpConnection,
      pool_maxsize=20,
      timeout = 10
    )

    # Check if index exist, if not, create one
    # if you create index, you need to wait a while, which is not cater in this code.
    if not self.client.indices.exists(index = self.index_name):
      settings = {
        "settings": {
          "index": {
            "knn": True,
          }
        },
        "mappings": {
          "properties": {
            "source": {"type": "text"},
            "page_number": {"type": "text"},
            "last_update_date": {"type": "text"},
            "text": {"type": "text"},
            "chunk": {"type": "integer"},
            "embedding": {
              "type": "knn_vector",
              "dimension": 1024,
              "method": {
                "name": "hnsw",
                "space_type": "innerproduct",
                "engine": "faiss",
                "parameters": {
                  "ef_construction": 256
                }
              }
            },
          }
        },
      }
      self.client.indices.create(index=index_name, body=settings)

  # CRUD >> READ
  def query(self, query, query_vector, k):
    # Hybrid search
    payload = {
      "query": {
        "bool": {
          "should": [
            {
              "script_score": {
                "query": {
                  "match": {
                    "text": query
                  }
                },
                "script": {
                  "source": "_score"
                }
              }
            },
            {
              "knn": {
                "embedding": {
                  "vector": query_vector,
                  "k": k
                }
              }
            }
          ]
        }
      }
    }

    docs =  self.client.search(body=payload, index=self.index_name)

    return docs['hits']['hits']

  # CRUD >> UPDATE
  def push_to_index(self, documents):
    """
    args:
        documents(list): list of dictionaries of documents
    """
    
    # Iterate and push to index
    for i, doc in enumerate(documents):
      document = {
        "source": doc["metadata"]["source"],
        "page_number": doc["metadata"]["page_number"],
        "last_update_date": doc["metadata"]["last_update_date"],
        "text": doc["text"],
        "chunk": i,
        "embedding": doc["embedding"]
      }
      # add everything to index
      response = self.client.index(
        index = self.index_name, 
        body = document
      )
      return response['result']
          
  # CRUD >> DELETE
  def delete_file(self, file_name):
    query = {
      'query': {
        'match': {
          "file_name": file_name
        }
      }
    }
    response = self.client.search(index =self.index_name, body =query, version = True)
    file_deleted = None

    id_list = [q['_id'] for q in response['hits']['hits']]
    for id in id_list:
      self.client.delete(
        index = self.index_name,
        id = id
      )
      file_deleted = True
    return file_deleted

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
      query = processing["config"]["query"] # TODO: To format based on message structure
      host = project_rag_opensearch__endpoint # TODO: To format based on message structure
      index_name = processing["config"]["index_name"] # TODO: To format based on message structure
      embedding = processing["config"]["embedding"] # TODO: To format based on message structure
      k = processing["config"]["k"] # TODO: To format based on message structure

      result = processing["result"]

      # i have no idea what this does, copy and paste from WeiXuan example
      fileindexer = FileIndexer(host, index_name)
      results = fileindexer.query(query, embedding, k)

      # SQS to next rag_flow_component
      # store is the last flow

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