import json
import logging
import time
import uuid
from datetime import datetime
from http import HTTPStatus
from typing import Dict

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from app.config import DATETIME_FORMAT
from app.utils.dynamodb_model import DynamodbModel

"""
Note: DynamoDB related functions always return a dictionary containing at least 'HTTPStatusCode' and 'Message'. 
"""

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


class OtpModel(DynamodbModel):
    INDEX_NAME_JWT = 'index_jwt'

    def __init__(self, dynamodb, table_name):
        super().__init__(dynamodb, table_name)
        self.dynamodb = dynamodb
        self.table_name = table_name
        self.table = dynamodb.Table(table_name)

        # Check if table exists
        try:
            self.table.table_status in (
                "CREATING", "UPDATING", "DELETING", "ACTIVE")
        except ClientError:
            logger.error(f"DynamoDB Table {table_name} doesn't exist.")
            raise

    def put_item(self, email: str, otp: str, others: Dict):
        """Save a record into database.
        Raise exception if the key already exists.
        """
        try:
            logger.info(f'Calling put_item({email}, {otp}, {others})')
            data = dict(others)
            data['email'] = email
            data['otp'] = otp
            data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            response = self.table.put_item(
                Item=data,
                ConditionExpression='email <> :email AND otp <> :otp',
                ExpressionAttributeValues={
                    ':email': email, ':otp': otp}
                # PutItem only allows ReturnValues="None"
            )
            logger.info(response)

            # Get the saved item
            response_get = self.get_item(email, otp)

            return {
                'Item': response_get['Item'],
                'HTTPStatusCode': HTTPStatus.OK,
                'Message': 'Put: Successful'}
        except ClientError as e:
            logger.error(e)
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {'HTTPStatusCode': HTTPStatus.FORBIDDEN,
                        'Message': f'Item already exists: email={email} & otp={otp}'}
            else:
                return {'HTTPStatusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                        'Message': f'{e}'}

    def update_item(self, email: str, otp: str, attributes: Dict):
        """Update a record with its key using partial attributes.
        """
        logger.info(
            f'Calling update_item(): email={email}, otp={otp} attributes={attributes}')
        try:
            # Cannot update email, otp. Always update updated_at
            params = [f'{key}=:{key}' for key in attributes.keys()]
            params.append('updated_at=:updated_at')
            expr = f"SET {', '.join(params)}"
            attr_vals = {f':{k}': v for k, v in attributes.items()}
            attr_vals[':email'] = email
            attr_vals[':otp'] = otp
            attr_vals[':updated_at'] = time.strftime(DATETIME_FORMAT)
            response = self.table.update_item(
                Key={'email': email, 'otp': otp},
                UpdateExpression=expr,
                ConditionExpression="email=:email AND otp=:otp",
                ExpressionAttributeValues=attr_vals,
                ReturnValues="ALL_NEW"
            )
            logger.info(response)
            return {'Item': response['Attributes'],
                    'HTTPStatusCode': response['ResponseMetadata']['HTTPStatusCode'],
                    'Message': 'Update: Successful'}
        except ClientError as ex:
            logger.error(ex)
            logger.info(ex.response)
            if ex.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {'HTTPStatusCode': HTTPStatus.NOT_FOUND,
                        'Message': f'Item not found: email={email} and otp={otp}'}
            else:
                return {'HTTPStatusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                        'Message': ex.response['Error']['Message']}

    def get_item(self, email: str, otp: str):
        """Get a record by its PK & SK.
        """
        logger.info(f'Calling get_item({email}, {otp})')
        try:
            response = self.table.get_item(
                Key={'email': email,
                     'otp': otp}
            )
            logger.info(response)
            return {'Item': response['Item'],
                    'HTTPStatusCode': response['ResponseMetadata']['HTTPStatusCode'],
                    'Message': 'Get: Successful'}
        except KeyError as e:
            logger.error(e)
            return {'HTTPStatusCode': HTTPStatus.NOT_FOUND,
                    'Message': f'Item not found with key: {email}, {otp}'}
        except ClientError as e:
            logger.error(e)
            return {'HTTPStatusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                    'Message': e.response['Error']['Message']}
        except Exception as e:
            logger.error(f'Unknown error: type={type(e)}, error={str(e)}')
            return {'HTTPStatusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                    'Message': str(e)}

    def delete_item(self, email: str, otp: str):
        """Delete a record by its PK & SK.
        """
        try:
            response = self.table.delete_item(
                Key={
                    'email': email,
                    'otp': otp
                },
                ReturnValues="ALL_OLD"
            )
            logger.info(response)
            return {'Item': response['Attributes'],
                    'Message': 'Delete: Successful',
                    'HTTPStatusCode': response['ResponseMetadata']['HTTPStatusCode']}
        except KeyError as e:
            logger.error(e)
            return {'HTTPStatusCode': HTTPStatus.NOT_FOUND,
                    'Message': f'Item not found with key: {email}, {otp}'}
        except ClientError as e:
            logger.error(e)
            if e.response['Error']['Code'] == "ConditionalCheckFailedException":
                return {'HTTPStatusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
                        'Message': e.response['Error']['Message']}
            else:
                raise

    def get_item_by_jwt(self, jwt: str):
        """Get a record using GSI message_id
        """
        logger.info(f'Calling get_item_by_jwt({jwt})')

        # Wait if global secondary indexes are being updated
        while True:
            if not self.table.global_secondary_indexes or self.table.global_secondary_indexes[0][
                'IndexStatus'] != 'ACTIVE':
                logger.info('Waiting for index to backfill...')
                time.sleep(5)
                self.table.reload()
            else:
                break

        # Query for records
        response = self.table.query(
            IndexName=self.INDEX_NAME_JWT,
            KeyConditionExpression=Key('jwt').eq(jwt)
        )
        logger.info(response)
        if 'Items' in response and response['Items']:
            return {'Item': response['Items'][0],
                    'HTTPStatusCode': response['ResponseMetadata']['HTTPStatusCode'],
                    'Message': 'Successful'}
        else:
            return {'HTTPStatusCode': HTTPStatus.NOT_FOUND,
                    'Message': f'Item not found: {jwt}'}

    def list_items_by_email(self, email: str):
        """List records from database using PK
        """
        params = {
            "KeyConditionExpression": Key('email').eq(email)
        }
        response = self.table.query(**params)
        logger.info(f"Count: {response.get('Count')}, ScannedCount: {response.get('ScannedCount')}")

        # DynamoDB returns max 1Mb of data, continue to query if LastEvaluatedKey exists
        data = response.get('Items', [])
        while response.get('LastEvaluatedKey'):
            params['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = self.table.query(**params)
            logger.info(f"Count: {response.get('Count')}, ScannedCount: {response.get('ScannedCount')}")
            data.extend(response.get('Items', []))

        if data:
            return {'Items': data,
                    'HTTPStatusCode': HTTPStatus.OK,
                    'Message': 'Successful'}
        else:
            return {'HTTPStatusCode': HTTPStatus.NOT_FOUND,
                    'Message': f'Items not found for email={email}'}


if __name__ == '__main__':
    from app import config

    TABLE_NAME = config.TABLE_WHITESPACE_USERS

    dynamodb = boto3.resource(
        "dynamodb",
        # endpoint_url=r'http://localhost:8000/'
    )
    user_model = OtpModel(dynamodb, TABLE_NAME)

    data = {'email': 'mark.qj@gmail.com', 'otp': '1234'}

    result = user_model.put_item(
        email=data['email'], otp=data['otp'], others={'name': 'Mark'})
    print("PUT:", result)

    result = user_model.get_item(data['email'], data['otp'])
    print("GET:", result)

    result = user_model.update_item(email=data['email'], otp=data['otp'],
                                    attributes={'name': 'Markov'})
    print("UPDATE:", result)

    result = user_model.get_item_by_jwt(
        jwt='1234567890')
    print(result)

    result = user_model.list_items_by_email(
        email=data['email'])
    print(result)

    result = user_model.delete_item(
        email=data['email'], otp=data['otp'])
    print("DELETE:", result)
