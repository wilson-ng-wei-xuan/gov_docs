import json
import boto3
import os

import util_tool # utility for generic tools

import logging
logging.getLogger().setLevel(logging.INFO)

import re
from pymongo import MongoClient, errors

def lambda_handler(event, context):
  logging.info('got event {}'.format( json.dumps(event) ))
  global function_name
  function_name = context.function_name

  """Secrets Manager MongoDB Handler

  This handler uses the single-user rotation scheme to rotate a MongoDB user credential. This rotation scheme
  logs into the database as the user and rotates the user's own password, immediately invalidating the user's
  previous password.

  The Secret SecretString is expected to be a JSON string with the following format:
  {
    'engine': <required: must be set to 'mongo'>,
    'host': <required: instance host name>,
    'username': <required: username>,
    'password': <required: password>,
    'dbname': <optional: database name>,
    'port': <optional: if not specified, default port 27017 will be used>
    'ssl': <optional: if not specified, defaults to false. This must be true if being used for DocumentDB rotations where the cluster has TLS enabled>
  }

  Args:
    event (dict): Lambda dictionary of event parameters. These keys must include the following:
      - SecretId: The secret ARN or identifier
      - ClientRequestToken: The ClientRequestToken of the secret version
      - Step: The rotation step (one of createSecret, setSecret, testSecret, or finishSecret)

    context (LambdaContext): The Lambda runtime information

  Raises:
    ResourceNotFoundException: If the secret with the specified arn and stage does not exist

    ValueError: If the secret is not properly configured for rotation

    KeyError: If the secret json does not contain the expected keys

  """
  arn = event['SecretId']
  token = event['ClientRequestToken']
  step = event['Step']

  # Setup the client
  secrets_client = boto3.client('secretsmanager')

  # Make sure the version is staged correctly
  metadata = secrets_client.describe_secret(SecretId=arn)
  if not metadata['RotationEnabled']:
    logging.error("Secret %s is not enabled for rotation" % arn)
    raise ValueError("Secret %s is not enabled for rotation" % arn)
  versions = metadata['VersionIdsToStages']

  if token not in versions:
    logging.error("Secret version %s has no stage for rotation of secret %s." % (token, arn))
    raise ValueError("Secret version %s has no stage for rotation of secret %s." % (token, arn))

  if "AWSCURRENT" in versions[token]:
    logging.info("Secret version %s already set as AWSCURRENT for secret %s." % (token.encode(), arn.encode()))
    return
  elif "AWSPENDING" not in versions[token]:
    logging.error("Secret version %s not set as AWSPENDING for rotation of secret %s." % (token, arn))
    raise ValueError("Secret version %s not set as AWSPENDING for rotation of secret %s." % (token, arn))

  if step == "createSecret":
    create_secret(secrets_client, arn, token)

  elif step == "setSecret":
    set_secret(secrets_client, arn, token)

  elif step == "testSecret":
    test_secret(secrets_client, arn, token)

  elif step == "finishSecret":
    finish_secret(secrets_client, arn, token)

  else:
    logging.error("lambda_handler: Invalid step parameter %s for secret %s" % (step, arn))
    raise ValueError("Invalid step parameter %s for secret %s" % (step, arn))

################################################################################
################################################################################
def create_secret(secrets_client, arn, token):
  """Create the secret

  This method first checks for the existence of a secret for the passed in token. If one does not exist, it will generate a
  new secret and put it with the passed in token.

  Args:
    secrets_client (client): The secrets manager service client

    arn (string): The secret ARN or other identifier

    token (string): The ClientRequestToken associated with the secret version

  Raises:
    ResourceNotFoundException: If the secret with the specified arn and stage does not exist

  """
  # Make sure the current secret exists
  new_secret = get_secret_dict(secrets_client, arn, "AWSCURRENT")
#  new_secret = json.loads( new_secret['SecretString'] )

  # Now try to get the secret version, if that fails, put a new secret
  try:
    get_secret_dict(secrets_client, arn, "AWSPENDING", token)
    logging.info("createSecret: Successfully retrieved secret for %s." % arn.encode())

  except secrets_client.exceptions.ResourceNotFoundException:
    # Get exclude characters from environment variable
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager/client/get_random_password.html
    # characters from the password: ! " # $ % & ' ( ) * + , - . / : ; < = > ? @ [ \ ] ^ _ ` { | } ~
    exclude_characters = os.environ['EXCLUDE_CHARACTERS'] if 'EXCLUDE_CHARACTERS' in os.environ else '!"#$%&\'()*+,./:;<=>?@[\\]^`{|}~'

    # Generate a random password
    passwd = secrets_client.get_random_password(PasswordLength=18,
                                                ExcludeCharacters=exclude_characters,
                                                ExcludeNumbers=False,
                                                ExcludePunctuation=False,
                                                ExcludeUppercase=False,
                                                ExcludeLowercase=False,
                                                IncludeSpace=False,
                                                RequireEachIncludedType=True)

    new_secret['password'] = passwd['RandomPassword']

    # Put the secret
    secrets_client.put_secret_value(SecretId=arn, ClientRequestToken=token, VersionStages=['AWSPENDING'],
                                    SecretString=json.dumps(  new_secret ) )

    logging.info("createSecret: Successfully put secret for ARN %s and version %s." % (arn.encode(), token.encode()))

################################################################################
################################################################################
def set_secret(secrets_client, arn, token):
  """Set the pending secret in the database

  This method tries to login to the database with the AWSPENDING secret and returns on success. If that fails, it
  tries to login with the AWSCURRENT and AWSPREVIOUS secrets. If either one succeeds, it sets the AWSPENDING password
  as the user password in the database. Else, it throws a ValueError.

  Args:
    service_client (client): The secrets manager service client

    arn (string): The secret ARN or other identifier

    token (string): The ClientRequestToken associated with the secret version

  Raises:
    ResourceNotFoundException: If the secret with the specified arn and stage does not exist

    ValueError: If the secret is not valid JSON or valid credentials are found to login to the database

    KeyError: If the secret json does not contain the expected keys

  """

  try:
    previous_dict = get_secret_dict(secrets_client, arn, "AWSPREVIOUS")

  except (secrets_client.exceptions.ResourceNotFoundException, KeyError):
    previous_dict = None
  current_dict = get_secret_dict(secrets_client, arn, "AWSCURRENT")
  pending_dict = get_secret_dict(secrets_client, arn, "AWSPENDING", token)

  # First try to login with the pending secret, if it succeeds, return
  conn = get_connection(pending_dict)
  if conn != None:
    # conn.logout() # https://pymongo.readthedocs.io/en/stable/migrate-to-pymongo4.html#database-authenticate-and-database-logout-are-removed
    logging.info("setSecret: AWSPENDING secret is already set as password in MongoDB for secret arn %s." % arn.encode())
    return

  # Make sure the user from current and pending match
  if current_dict['username'] != pending_dict['username']:
    logging.error("setSecret: Attempting to modify user %s other than current user %s" % (pending_dict['username'], current_dict['username']))
    raise ValueError("Attempting to modify user %s other than current user %s" % (pending_dict['username'], current_dict['username']))

  # Make sure the host from current and pending match
  if current_dict['host'] != pending_dict['host']:
    logging.error("setSecret: Attempting to modify user for host %s other than current host %s" % (pending_dict['host'], current_dict['host']))
    raise ValueError("Attempting to modify user for host %s other than current host %s" % (pending_dict['host'], current_dict['host']))

  # Now try the current password
  conn = get_connection(current_dict)
  # If both current and pending do not work, try previous
  if conn == None and previous_dict:
    # Update previous_dict to leverage current SSL settings
    previous_dict.pop('ssl', None)
    if 'ssl' in current_dict:
      previous_dict['ssl'] = current_dict['ssl']

    conn = get_connection(previous_dict)

    # Make sure the user/host from previous and pending match
    if previous_dict['username'] != pending_dict['username']:
      logging.error("setSecret: Attempting to modify user %s other than previous valid user %s" % (pending_dict['username'], previous_dict['username']))
      raise ValueError("Attempting to modify user %s other than previous valid user %s" % (pending_dict['username'], previous_dict['username']))

    if previous_dict['host'] != pending_dict['host']:
      logging.error("setSecret: Attempting to modify user for host %s other than previous host %s" % (pending_dict['host'], previous_dict['host']))
      raise ValueError("Attempting to modify user for host %s other than previous host %s" % (pending_dict['host'], previous_dict['host']))

  # If we still don't have a connection, raise a ValueError
  if conn == None:
    logging.error("setSecret: Unable to log into database with previous, current, or pending secret of secret arn %s" % arn)
    raise ValueError("Unable to log into database with previous, current, or pending secret of secret arn %s" % arn)

  # Now set the password to the pending password
  try:
    conn.command("updateUser", pending_dict['username'], pwd=pending_dict['password'])
    logging.info("setSecret: Successfully set password for user %s in MongoDB for secret arn %s." % (pending_dict['username'], arn.encode()))

  except errors.PyMongoError:
    logging.error("setSecret: Error encountered when attempting to set password in database for user %s", pending_dict['username'])
    raise ValueError("Error encountered when attempting to set password in database for user %s", pending_dict['username'])

  finally:
    print("Fake logout")
    # conn.logout() # https://pymongo.readthedocs.io/en/stable/migrate-to-pymongo4.html#database-authenticate-and-database-logout-are-removed

  # proceed to restart the task

  # This is where the secret should be set in the service
  # dissecting SecretARN to get project-code
  # arn:aws:secretsmanager:ap-southeast-1:003031427344:secret:secret-uatez-appraiser-project-YhU2MD
  secret_id = arn.split(':')[-1] # secret-uatez-appraiser-project-YhU2MD
  project_code = secret_id.split('-')[2] # appraiser
  secret_name = '-'.join( secret_id.split('-')[:-1] ) # secret-uatez-appraiser-project

  ecs_client = boto3.client('ecs')

  list_clusters = ecs_client.list_clusters()
  clusters = [arn for arn in list_clusters['clusterArns'] if project_code in arn]

  # for each cluster of the project code
  for cluster in clusters:
    list_tasks = ecs_client.list_tasks(
      cluster=cluster,
      launchType='FARGATE'
    )

    # try to get the list of taskarn, in case there are no running task
    try:
      tasks = ecs_client.describe_tasks(
        cluster = cluster,
        tasks = list_tasks['taskArns']
      )

      restarted_svc = []

      # get the task definition
      for task in tasks['tasks']:
        task_definition = ecs_client.describe_task_definition(
          taskDefinition = task['taskDefinitionArn']
        )

        # look into the containerDefinitions
        for containerDefinition in task_definition['taskDefinition']['containerDefinitions']:

          # check the environment
          for kv_pair in containerDefinition['environment']:

            # if the value matches the secret_name
            if kv_pair['value'] == secret_name:
              service = task['group'].replace("service:", "")

              if service not in restarted_svc:
                print( "match!" )
  
                restarted_svc.append( service )

                # stop the service for it to restart
                logging.info("setSecret: Force New Deployment service: %s" % (service))
                stop_task = ecs_client.update_service(
                  cluster = cluster,
                  service = service,
                  forceNewDeployment=True
                )
                
                logging.info("setSecret: Successfully Force New Deployment service")
                print( f"[NOTIFY] {function_name} restarted {service}" )

              else:
                logging.info("setSecret:  Already Redeploying service: %s" % (service))

    except Exception as e:
      if 'when calling the DescribeTasks operation: Tasks cannot be empty.' in str(e):
        logging.info('{} cannot describe_tasks for {} >> {}'.format( function_name, cluster, str(e) ) ) # sends to the channel

      else:
        logging.warn('{} cannot describe_tasks for {} >> {}'.format( function_name, cluster, str(e) ) ) # sends to the channel

  logging.info("setSecret: Done checking")

################################################################################
################################################################################
def test_secret(secrets_client, arn, token):
  """Test the secret

  This method should validate that the AWSPENDING secret works in the service that the secret belongs to. For example, if the secret
  is a database credential, this method should validate that the user can login with the password in AWSPENDING and that the user has
  all of the expected permissions against the database.

  If the test fails, this function should raise an exception. (Any exception.)
  If no exception is raised, the test is considered to have passed. (The return value is ignored.)

  Args:
    secrets_client (client): The secrets manager service client

    arn (string): The secret ARN or other identifier

    token (string): The ClientRequestToken associated with the secret version

  """
  # This is where the secret should be tested against the service
  logging.info("testSecret: Proceed to next step.")

################################################################################
################################################################################
def finish_secret(secrets_client, arn, token):
  """Finish the secret

  This method finalizes the rotation process by marking the secret version passed in as the AWSCURRENT secret.

  Args:
      secrets_client (client): The secrets manager service client

      arn (string): The secret ARN or other identifier

      token (string): The ClientRequestToken associated with the secret version

  Raises:
      ResourceNotFoundException: If the secret with the specified arn does not exist

  """
  # First describe the secret to get the current version
  metadata = secrets_client.describe_secret(SecretId=arn)
  current_version = None
  for version in metadata["VersionIdsToStages"]:
    if "AWSCURRENT" in metadata["VersionIdsToStages"][version]:
      if version == token:
        # The correct version is already marked as current, return
        logging.info("finishSecret: Version %s already marked as AWSCURRENT for %s" % (version.encode(), arn.encode()))
        return
      current_version = version
      break

  # Finalize by staging the secret version current
  secrets_client.update_secret_version_stage(SecretId=arn, VersionStage="AWSCURRENT", MoveToVersionId=token, RemoveFromVersionId=current_version)
  logging.info("finishSecret: Successfully set AWSCURRENT stage to version %s for secret %s." % (token.encode(), arn.encode()))

################################################################################
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
    client = MongoClient(host=host, port=27017, connectTimeoutMS=5000, serverSelectionTimeoutMS=5000, ssl=use_ssl,
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