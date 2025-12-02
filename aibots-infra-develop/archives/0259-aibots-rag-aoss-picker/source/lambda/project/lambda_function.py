import json
import os
import boto3
import datetime

import logging
logging.getLogger().setLevel(logging.INFO)

import requests
from requests_aws4auth import AWS4Auth

aoss_client = boto3.client('opensearchserverless')
cw_client = boto3.client('cloudwatch')

region = os.environ['AWS_REGION']
service = 'aoss'

def lambda_handler(event, context):
  logging.info('got event {}'.format( json.dumps(event) ))

  aws_account_id = context.invoked_function_arn.split(":")[4]

  EndTime   = datetime.datetime.now()
  StartTime = EndTime - datetime.timedelta( minutes = 1 )

  credentials = boto3.Session().get_credentials()
  awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

  collections = aoss_client.list_collections(
    collectionFilters={
      'status': 'ACTIVE'
    },
  )

  print( json.dumps(collections, default = str) )

  for collection in collections['collectionSummaries']:
    url = 'https://' + collection['id'] + '.' + region + '.' + service + '.amazonaws.com' + '/_cat/indices'
    print( url )
    headers = {"Content-Type": "application/json"}
    r = requests.get(url, auth=awsauth, headers=headers)
    print(r.status_code)
    print(r.text)

    url = 'https://' + collection['id'] + '.' + region + '.' + service + '.amazonaws.com' + '/_cat/indices?v=true'
    print( url )
    headers = {"Content-Type": "application/json"}
    r = requests.get(url, auth=awsauth, headers=headers)
    print(r.status_code)
    print(r.text)

    url = 'https://' + collection['id'] + '.' + region + '.' + service + '.amazonaws.com' + '/_cat/_stats'
    print( url )
    headers = {"Content-Type": "application/json"}
    r = requests.get(url, auth=awsauth, headers=headers)
    print(r.status_code)
    print(r.text)

    # StorageUsed = cw_client.get_metric_statistics(
    #   Namespace = 'AWS/AOSS',
    #   MetricName = 'StorageUsedInS3',
    #   Dimensions=[
    #     {
    #         'Name': 'CollectionName',
    #         'Value': collection['name']
    #     },
    #     {
    #         'Name': 'CollectionId',
    #         'Value': collection['id']
    #     },
    #     {
    #         'Name': 'ClientId',
    #         'Value': aws_account_id
    #     }
    #   ],
    #   StartTime = StartTime,
    #   EndTime   = EndTime,
    #   Period    = 1,
    #   Statistics = ['Sum']
    # )

    # Documents = cw_client.get_metric_statistics(
    #   Namespace = 'AWS/AOSS',
    #   MetricName = 'SearchableDocuments',
    #   Dimensions=[
    #     {
    #         'Name': 'CollectionName',
    #         'Value': collection['name']
    #     },
    #     {
    #         'Name': 'CollectionId',
    #         'Value': collection['id']
    #     },
    #     {
    #         'Name': 'ClientId',
    #         'Value': aws_account_id
    #     }
    #   ],
    #   StartTime = StartTime,
    #   EndTime   = EndTime,
    #   Period    = 1,
    #   Statistics = ['Sum']
    # )

    # print( json.dumps(Documents, default = str) )

  logging.info('event ended.')
  return { 
    'message' : 'event ended.'
  }