import json
import boto3
import os
import re

import logging
logging.getLogger().setLevel(logging.INFO)

from pymongo import MongoClient, errors

project_db__secret = os.environ['PROJECT_DB__SECRET']

secrets_client = boto3.client('secretsmanager')
sqs_client = boto3.client('sqs')

rag_flow = os.environ['RAG_FLOW']
rag_flow_component = os.environ['RAG_FLOW_COMPONENT']

def lambda_handler(event, context):
  # TODO implement
  # Everything is in the event
  logging.info('got event {}'.format( json.dumps(event) ))

  # Do what you need to do
  try:
    # https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html
    batch_item_failures = []
    sqs_batch_response = {}

    # Make sure the current secret exists
    current_dict = get_secret_dict(secrets_client, project_db__secret, "AWSCURRENT")
    # get a connection
    conn = get_connection(current_dict)
    # try to Mongo by listing databases
    conn.command( "listDatabases" )

    # loop into the SQS payload, can contain up to 10 records.
    for idx, record in enumerate( event['Records'] ):
      logging.info('processing SNS record {} of {}'.format( idx+1, len( event['Records'] ) ) )

      ##########################################################################
      # # processing sqs message
      ##########################################################################
      try:
        message = json.loads( record['body'] )
        logging.info('{}'.format( json.dumps(message) ))

        # process the SQS message here.
        # YOU SHALL ADD YOUR LOGIC HERE
        bot_id    = message["bot_id"]
        doc_id    = message["doc_id"]
        action    = message["action"]
        flow      = message[rag_flow][rag_flow_component]["flow"]
        component = message[rag_flow][rag_flow_component]["component"]
        dts       = message[rag_flow][rag_flow_component]["dts"]
        status    = message[rag_flow][rag_flow_component]["status"]
        reason    = message[rag_flow][rag_flow_component]["reason"]

      except Exception as e:
        # when there is error processing the message
        # log error to send to slack
        logging.error( '{} >> error processing sqs message >> {}'.format( context.function_name, str(e) ) ) # sends to the channel
        # inform SQS this message failed to process at the end
        batch_item_failures.append({"itemIdentifier": record['messageId']})
        continue # proceed to next record

      ##########################################################################
      # # updating the status
      ##########################################################################
      try:
        # run pymongo command to update status.
        response = conn.command( "listDatabases" )
        logging.info( "Successfully update status." )
        logging.info('{}'.format( json.dumps(response, default = str) ))

      except errors.PyMongoError:
        # log error to send to slack
        logging.error('sqs message ended with error, fail to update status.')
        # inform SQS this message failed to process at the end
        batch_item_failures.append( { "itemIdentifier": record['messageId'] } )
        continue # to next record

      ##########################################################################

  # except errors.PyMongoError:
  except Exception as e:
    logging.error('sqs batch error, fail to connect to MongoDB.')

    # https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html#services-sqs-batchfailurereporting
    # We can't connect to Mongo, so no point continue, just fail whole batch.
    # An empty string itemIdentifier to fail whole batch
    logging.info("returning >> ")
    logging.info( { "batchItemFailures": [ { "itemIdentifier": "" } ] } )
    return { "batchItemFailures": [ { "itemIdentifier": "" } ] }

  # conn.logout() # deprecated
  # https://pymongo.readthedocs.io/en/stable/migrate-to-pymongo4.html#database-authenticate-and-database-logout-are-removed

  # This return will tell SQS to retry which failed message.
  # default all pass will return { "batchItemFailures": [] }
  sqs_batch_response["batchItemFailures"] = batch_item_failures
  logging.info("returning >> ")
  logging.info(sqs_batch_response)
  return sqs_batch_response

################################################################################
# # The following chucks of codes were copies from old secret-rotator.
# # https://github.com/aws-samples/aws-secrets-manager-rotation-lambdas/blob/master/SecretsManagerMongoDBRotationSingleUser/lambda_function.py
################################################################################
def get_connection(secret_dict):
  """Gets a connection to MongoDB from a secret dictionary

  This helper function uses connectivity information from the secret dictionary to initiate
  connection attempt(s) to the database. Will attempt a fallback, non-SSL connection when
  initial connection fails using SSL and fall_back is True.

  Args:
    secret_dict (dict): The Secret Dictionary

  Returns:
    Connection: The pymongo.database.Database object if successful. None otherwise

  Raises:
    KeyError: If the secret json does not contain the expected keys

  """
  # Parse and validate the secret JSON string
  port = int(secret_dict['port']) if 'port' in secret_dict else 27017
  dbname = secret_dict['dbname'] if 'dbname' in secret_dict else "admin"

  # Get SSL connectivity configuration
  use_ssl, fall_back = get_ssl_config(secret_dict)

  host = secret_dict['host'].split('/')[2].split(':')[0]

  # if an 'ssl' key is not found or does not contain a valid value, attempt an SSL connection and fall back to non-SSL on failure
  conn = connect_and_authenticate(secret_dict, host, port, dbname, use_ssl)

  if conn != None or not fall_back:
    return conn
  else:
    return connect_and_authenticate(secret_dict, host, port, dbname, False)

################################################################################
################################################################################
def get_ssl_config(secret_dict):
  """Gets the desired SSL and fall back behavior using a secret dictionary

  This helper function uses the existance and value the 'ssl' key in a secret dictionary
  to determine desired SSL connectivity configuration. Its behavior is as follows:
    - 'ssl' key DNE or invalid type/value: return True, True
    - 'ssl' key is bool: return secret_dict['ssl'], False
    - 'ssl' key equals "true" ignoring case: return True, False
    - 'ssl' key equals "false" ignoring case: return False, False

  Args:
    secret_dict (dict): The Secret Dictionary

  Returns:
    Tuple(use_ssl, fall_back): SSL configuration
      - use_ssl (bool): Flag indicating if an SSL connection should be attempted
      - fall_back (bool): Flag indicating if non-SSL connection should be attempted if SSL connection fails

  """
  # Default to True for SSL and fall_back mode if 'ssl' key DNE
  if 'ssl' not in secret_dict:
    return True, True

  # Handle type bool
  if isinstance(secret_dict['ssl'], bool):
    return secret_dict['ssl'], False

  # Handle type string
  if isinstance(secret_dict['ssl'], str):
    ssl = secret_dict['ssl'].lower()
    if ssl == "true":
      return True, False
    elif ssl == "false":
      return False, False
    else:
      # Invalid string value, default to True for both SSL and fall_back mode
      return True, True

  # Invalid type, default to True for both SSL and fall_back mode
  return True, True

################################################################################
################################################################################
def connect_and_authenticate(secret_dict, host, port, dbname, use_ssl):
  """Attempt to connect and authenticate to a MongoDB instance

  This helper function tries to connect to the database using connectivity info passed in.
  If successful, it returns the connection, else None

  Args:
    - secret_dict (dict): The Secret Dictionary
    - port (int): The databse port to connect to
    - dbname (str): Name of the database
    - use_ssl (bool): Flag indicating whether connection should use SSL/TLS

  Returns:
    Connection: The pymongo.database.Database object if successful. None otherwise

  Raises:
    KeyError: If the secret json does not contain the expected keys

  """
  # Try to obtain a connection to the db
  try:
    # Hostname verfification and server certificate validation enabled by default when ssl=True
    # client = MongoClient(host=secret_dict['host'], port=port, connectTimeoutMS=5000, serverSelectionTimeoutMS=5000, ssl=use_ssl)
    client = MongoClient(host=host, port=port, connectTimeoutMS=5000, serverSelectionTimeoutMS=5000, ssl=use_ssl,
      username=secret_dict['username'], password=secret_dict['password']
    )
    db = client[dbname]
    # db.authenticate(secret_dict['username'], secret_dict['password']) # https://pymongo.readthedocs.io/en/stable/migrate-to-pymongo4.html#database-authenticate-and-database-logout-are-removed
    db.list_collection_names()

    logging.info("Successfully established %s connection as user '%s' with host: '%s'" % ("SSL/TLS" if use_ssl else "non SSL/TLS", secret_dict['username'], secret_dict['host']))
    return db

  except errors.PyMongoError as e:
    if 'SSL handshake failed' in e.args[0]:
      logging.error("Unable to establish SSL/TLS handshake, check that SSL/TLS is enabled on the host: %s" % secret_dict['host'])

    elif re.search("hostname '.+' doesn't match", e.args[0]):
      logging.error("Hostname verification failed when estlablishing SSL/TLS Handshake with host: %s" % secret_dict['host'])

    elif re.search("Authentication failed", e.args[0]):
      # this is by default not flagged in the AWS provided script.
      # but because i want to log all error in else
      # I just need to filter this Authentication failed.
      logging.info("Authentication failed: %s" % secret_dict['host'])

    else:
      logging.error( str(e) )

    return None

################################################################################
################################################################################
def get_secret_dict(service_client, arn, stage, token=None):
  """Gets the secret dictionary corresponding for the secret arn, stage, and token

  This helper function gets credentials for the arn and stage passed in and returns the dictionary by parsing the JSON string

  Args:
    service_client (client): The secrets manager service client

    arn (string): The secret ARN or other identifier

    token (string): The ClientRequestToken associated with the secret version, or None if no validation is desired

    stage (string): The stage identifying the secret version

  Returns:
    SecretDictionary: Secret dictionary

  Raises:
    ResourceNotFoundException: If the secret with the specified arn and stage does not exist

    ValueError: If the secret is not valid JSON

  """
  required_fields = ['host', 'username', 'password']

  # Only do VersionId validation against the stage if a token is passed in
  if token:
    secret = service_client.get_secret_value(SecretId=arn, VersionId=token, VersionStage=stage)
  else:
    secret = service_client.get_secret_value(SecretId=arn, VersionStage=stage)
  plaintext = secret['SecretString']
  secret_dict = json.loads(plaintext)

  # Run validations against the secret
  if 'engine' not in secret_dict or secret_dict['engine'] != 'mongo':
    raise KeyError("Database engine must be set to 'mongo' in order to use this rotation lambda")
  for field in required_fields:
    if field not in secret_dict:
      raise KeyError("%s key is missing from secret JSON" % field)

  # Parse and return the secret JSON string
  return secret_dict