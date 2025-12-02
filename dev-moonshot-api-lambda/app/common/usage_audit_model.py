"""
Note: DynamoDB related functions always return a dictionary containing at least 'HTTPStatusCode' and 'Message'.
"""

import time
from http import HTTPStatus
from typing import Optional

import pytz as pytz
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from pydantic import BaseModel, root_validator

from app.common.datetime_util import SG_TIMEZONE, get_curr_dt_str
from app.config import DATE_FORMAT, logger, DATETIME_TZ_FORMAT, TABLE_USAGE_AUDIT
from app.utils.dynamodb_model import DynamodbModel
from app.utils.file_util import hash_by_md5

sg_timezone = pytz.timezone(SG_TIMEZONE)


class UsageAuditType(BaseModel):
    """
    Model for DynamoDB table to keep track of usage of whitespace project sites
        PK: session_hash, SK: session_datetime
        GSI (index_site_date): GSI-PK: site_name, GSI-SK: usage_date
    """
    session_hash: Optional[str]  # PK = MD5 hash of site_name + ip + user_agent
    session_datetime: Optional[str]  # SK
    site_name: str  # GSI-PK
    usage_date: Optional[str]  # GSI-SK
    ip: Optional[str]
    user_agent: Optional[str]
    request_data: Optional[str]

    @root_validator
    @classmethod
    def validate_all(cls, values):
        if not values.get('session_datetime'):
            values['session_datetime'] = get_curr_dt_str(dt_format=DATETIME_TZ_FORMAT)
        if not values.get('usage_date'):
            values['usage_date'] = get_curr_dt_str(dt_format=DATE_FORMAT, timezone_val='Asia/Singapore')
        if not values.get('session_hash'):
            session_str = f'{values.get("site_name")} {values.get("ip")} {values.get("user_agent")}'
            values['session_hash'] = hash_by_md5(session_str)
        return values

    class Config:
        """
        Model configuration and example object
        """
        # Use enum value instead of enum object
        use_enum_values = True
        schema_extra = {
            "example": {
                "site_name": 'zorua',
                "ip": '127.0.0.1',
                "user_agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36',
                "request_data": '',
            }
        }


class UsageAuditModel(DynamodbModel):
    """
    DynamoDB model for usage_audit table
    """

    INDEX_SITE_DATE = 'index_site_date'

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

    def put_item(self, item: UsageAuditType):
        """Save a record into database.
        Raise exception if the key already exists.
        """
        try:
            logger.info(f'Calling put_item(): item = {item}')

            response = self.table.put_item(
                Item=item.dict(),
                ConditionExpression='session_hash <> :session_hash AND session_datetime <> :session_datetime',
                ExpressionAttributeValues={
                    ':session_hash': item.session_hash, ':session_datetime': item.session_datetime}
                # PutItem only allows ReturnValues="None"
            )
            logger.info(response)

            return {
                'HTTPStatusCode': response['ResponseMetadata']['HTTPStatusCode'],
                'Message': 'Put: Successful'}
        except ClientError as e:
            logger.error(e)
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {'HTTPStatusCode': 403,
                        'Message': f'Item already exists: session_hash={item.session_hash} & session_datetime={item.session_datetime}'}
            else:
                return {'HTTPStatusCode': 500,
                        'Message': f'{e}'}

    def get_item(self, session_hash: str, session_datetime: str):
        """Get a record by its PK & SK.
        """
        logger.info(f'Calling get_item({session_hash}, {session_datetime})')
        try:
            response = self.table.get_item(
                Key={'session_hash': session_hash, 'session_datetime': session_datetime}
            )
            logger.info(response)
            return {'Item': response['Item'],
                    'HTTPStatusCode': response['ResponseMetadata']['HTTPStatusCode'],
                    'Message': 'Get: Successful'}
        except KeyError as e:
            logger.error(e)
            return {'HTTPStatusCode': 404,
                    'Message': f'Item not found with key: {session_hash}, {session_datetime}'}
        except ClientError as e:
            logger.error(e)
            return {'HTTPStatusCode': 500,
                    'Message': e.response['Error']['Message']}
        except Exception as e:
            logger.error(f'Unknown error: type={type(e)}, error={str(e)}')
            return {'HTTPStatusCode': 500,
                    'Message': str(e)}

    def delete_item(self, session_hash: str, session_datetime: str):
        """Delete a record by its PK & SK.
        """
        logger.info(f'Calling delete_item({session_hash}, {session_datetime})')
        try:
            response = self.table.delete_item(
                Key={
                    'session_hash': session_hash,
                    'session_datetime': session_datetime
                },
                ReturnValues="ALL_OLD"
            )
            logger.info(response)
            return {'Item': response['Attributes'],
                    'Message': 'Delete: Successful',
                    'HTTPStatusCode': response['ResponseMetadata']['HTTPStatusCode']}
        except KeyError as e:
            logger.error(e)
            return {'HTTPStatusCode': 404,
                    'Message': f'Item not found with key: {session_hash}, {session_datetime}'}
        except ClientError as e:
            logger.error(e)
            if e.response['Error']['Code'] == "ConditionalCheckFailedException":
                return {'HTTPStatusCode': 500,
                        'Message': e.response['Error']['Message']}
            else:
                raise

    def list_items_by_session_hash(self, session_hash: str):
        """List record from database using PK
        """
        params = {
            'KeyConditionExpression': Key('session_hash').eq(session_hash)
        }
        response = self.table.query(**params)
        logger.info(f"Count: {response.get('Count')}, ScannedCount: {response.get('ScannedCount')}")

        # DynamoDB returns max 1Mb of data, continue to query if LastEvaluatedKey exists
        data = response.get('Items', [])
        while response.get('LastEvaluatedKey'):
            params['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = self.table.query(**params)
            logger.info(f"Count: {response.get('Count')}, ScannedCount: {response.get('ScannedCount')}")
            data.extend(response['Items'])

        if data:
            return {'Items': data,
                    'HTTPStatusCode': HTTPStatus.OK,
                    'Message': 'Successful'}
        else:
            return {'HTTPStatusCode': 404,
                    'Message': f'Items not found for session_hash={session_hash}'}

    def list_items_by_site_and_date(self, site_name: str, usage_date: str):
        """List records using GSI site_name and usage_date
        """
        logger.info(
            f'Calling list_items_by_site_and_date({site_name}, {usage_date})')

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
        params = {
            'IndexName': self.INDEX_SITE_DATE,
            'KeyConditionExpression': 'site_name = :site_name AND usage_date = :usage_date',
            'ExpressionAttributeValues': {
                ':site_name': site_name,
                ":usage_date": usage_date,
            }
        }
        response = self.table.query(**params)
        logger.info(f"Count: {response.get('Count')}, ScannedCount: {response.get('ScannedCount')}")

        # DynamoDB returns max 1Mb of data, continue to query if LastEvaluatedKey exists
        data = response.get('Items', [])
        while response.get('LastEvaluatedKey'):
            params['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = self.table.query(**params)
            logger.info(f"Count: {response.get('Count')}, ScannedCount: {response.get('ScannedCount')}")
            data.extend(response['Items'])

        if data:
            return {'Items': data,
                    'HTTPStatusCode': response['ResponseMetadata']['HTTPStatusCode'],
                    'Message': 'Successful'}
        else:
            return {'HTTPStatusCode': 404,
                    'Message': f'Item not found: {site_name} & {usage_date}'}

    def list_items_by_site(self, site_name: str):
        """List all records for a site_name
        """
        logger.info(f'Calling list_items_by_site({site_name})')

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
        params = {
            'IndexName': self.INDEX_SITE_DATE,
            'KeyConditionExpression': 'site_name = :site_name',
            'ExpressionAttributeValues': {
                ":site_name": site_name,
            }
        }
        response = self.table.query(**params)
        logger.info(f"Count: {response.get('Count')}, ScannedCount: {response.get('ScannedCount')}")

        # DynamoDB returns max 1Mb of data, continue to query if LastEvaluatedKey exists
        data = response.get('Items', [])
        while response.get('LastEvaluatedKey'):
            params['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = self.table.query(**params)
            logger.info(f"Count: {response.get('Count')}, ScannedCount: {response.get('ScannedCount')}")
            data.extend(response['Items'])

        if data:
            return {'Items': data,
                    'HTTPStatusCode': response['ResponseMetadata']['HTTPStatusCode'],
                    'Message': 'Successful'}
        else:
            return {'HTTPStatusCode': 404,
                    'Message': f'Item not found: {site_name}'}


# FOR TESTING
if __name__ == '__main__':
    import boto3

    dynamodb = boto3.resource(
        "dynamodb",
        # endpoint_url=r'http://localhost:8000/'
    )
    model = UsageAuditModel(dynamodb, TABLE_USAGE_AUDIT)

    message = {
        "site_name": 'zorua',
        "ip": '127.0.0.1',
        "user_agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36',
        "request_data": '',
    }

    item = UsageAuditType(**message)
    print(item.dict())

    result = model.put_item(item=item)
    print("PUT:", result)

    result = model.get_item(session_hash='beffc176a4f1cb9174f3dc425dbbe4f6',
                            session_datetime='2022-05-09T07:33:39+0000')
    print("GET:", result)

    # result = model.list_items_by_session_hash(session_hash='beffc176a4f1cb9174f3dc425dbbe4f6')
    # print('list_items_by_session_hash():', result)

    result = model.list_items_by_site(site_name='zorua')
    print('list_items_by_site():', result)

    result = model.list_items_by_site_and_date(
        site_name='zorua', usage_date='2022-05-10')
    print("list_items_by_site_and_date():", result)
