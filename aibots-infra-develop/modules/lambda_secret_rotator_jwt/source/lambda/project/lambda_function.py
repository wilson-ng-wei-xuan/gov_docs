import json
import boto3
import os

import util_tool # utility for generic tools

import logging
logging.getLogger().setLevel(logging.INFO)

def lambda_handler(event, context):
  logging.info('got event {}'.format( json.dumps(event) ))
  global function_name
  function_name = context.function_name

  """Secrets Manager Rotation Template
  This is a template for creating an AWS Secrets Manager rotation lambda

  Args:
    event (dict): Lambda dictionary of event parameters. These keys must include the following:
      - SecretId: The secret ARN or identifier
      - ClientRequestToken: The ClientRequestToken of the secret version
      - Step: The rotation step (one of createSecret, setSecret, testSecret, or finishSecret)

    context (LambdaContext): The Lambda runtime information

  Raises:
    ResourceNotFoundException: If the secret with the specified arn and stage does not exist

    ValueError: If the secret is not properly configured for rotation

    KeyError: If the event parameters do not contain the expected keys

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
    logging.info("Secret version %s already set as AWSCURRENT for secret %s." % (token.encode(), arn.encode() ))
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
  new_secret = secrets_client.get_secret_value(SecretId=arn, VersionStage="AWSCURRENT")
  new_secret = json.loads( new_secret['SecretString'] )

  # Now try to get the secret version, if that fails, put a new secret
  try:
    secrets_client.get_secret_value(SecretId=arn, VersionId=token, VersionStage="AWSPENDING")
    logging.info("createSecret: Successfully retrieved secret for %s." % arn.encode())
    
  except secrets_client.exceptions.ResourceNotFoundException:
    # Get exclude characters from environment variable
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager/client/get_random_password.html
    # characters from the password: ! " # $ % & ' ( ) * + , - . / : ; < = > ? @ [ \ ] ^ _ ` { | } ~
    exclude_characters = os.environ['EXCLUDE_CHARACTERS'] if 'EXCLUDE_CHARACTERS' in os.environ else '!"#$%&\'()*+,./:;<=>?@[\\]^`{|}~'

    # Generate a random password
    passwd = secrets_client.get_random_password(PasswordLength=64,
                                                ExcludeCharacters=exclude_characters,
                                                ExcludeNumbers=False,
                                                ExcludePunctuation=False,
                                                ExcludeUppercase=False,
                                                ExcludeLowercase=False,
                                                IncludeSpace=False,
                                                RequireEachIncludedType=True)

    new_secret['JWT'] = passwd['RandomPassword']

    # Put the secret
    secrets_client.put_secret_value(SecretId=arn, ClientRequestToken=token, VersionStages=['AWSPENDING'],
                                    SecretString=json.dumps(  new_secret ) )

    logging.info("createSecret: Successfully put secret for ARN %s and version %s." % (arn.encode(), token.encode()))

################################################################################
################################################################################
def set_secret(secrets_client, arn, token):
  """Set the secret

  This method should set the AWSPENDING secret in the service that the secret belongs to. For example, if the secret is a database
  credential, this method should take the value of the AWSPENDING secret and set the user's password to this value in the database.

  Args:
    secrets_client (client): The secrets manager service client

    arn (string): The secret ARN or other identifier

    token (string): The ClientRequestToken associated with the secret version

  """
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