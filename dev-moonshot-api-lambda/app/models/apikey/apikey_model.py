import logging
import datetime
from uuid import uuid4
from decimal import Decimal
from http import HTTPStatus

import boto3
from boto3.dynamodb import conditions
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from app.config import TABLE_MOONSHOT_APIKEY, DATETIME_TZ_FORMAT
from app.utils import llm_util
from app.utils.dynamodb_model import DynamodbModel
from app.utils.query_util import (delete_item_handling, get_item_handling,
                                  get_return_status, put_item_handling, query_all_items, scan_all_items,
                                  remove_attributes, update_item_handling)
"""
DynamoDB related functions always return a dictionary containing at least 'HTTPStatusCode' and 'Message'. 
"""

from app.config import logger


class ApikeyModel(DynamodbModel):
    INDEX_SORT_BY_EMAIL_CREATED = 'index_apikey_email_created'
    INDEX_SORT_BY_PROJECT = 'index_apikey_project'

    def __init__(self, dynamodb, table_name):
        super().__init__(dynamodb, table_name)
        self.dynamodb = dynamodb
        self.table_name = table_name
        self.table = dynamodb.Table(table_name)

    def get_item(self, api_key: str):
        response = self.table.get_item(Key={'api_key':api_key})

        if not response.get('Item'):
            return None

        return {'Item': response.get('Item')}
                                          
    def put_item(self, api_key, email, enabled, project, agency):
        """
        Store api_key and additional params into DynamoDB
        """      
        create_time = datetime.datetime.utcnow().strftime(DATETIME_TZ_FORMAT)

        response = self.table.put_item(
            Item={
                'api_key':api_key,
                "email": email,
                "enabled": enabled,
                "project": project,
                "agency": agency,
                "created": create_time,
            },
            ConditionExpression="api_key <> :api_key",
            ExpressionAttributeValues={':api_key': api_key},
        )

        # Get the saved item
        return self.get_item(api_key)

    def update_item(self, api_key, email, enabled, project, agency):
        """
        Update api_key and additional params into DynamoDB
        """      
        update_time = datetime.datetime.utcnow().strftime(DATETIME_TZ_FORMAT)

        response = self.table.update_item(
            Key={
                'api_key':api_key,
            },
            UpdateExpression="set email=:email, enabled=:enabled, project=:project, agency=:agency, updated=:updated",
            ExpressionAttributeValues={
                ':email': email,
                ':enabled': enabled,
                ':project': project,
                ':agency': agency,
                ':updated': update_time,
            },
            ReturnValues="UPDATED_NEW"
        )

        # Get the saved item
        return self.get_item(api_key)
    
    def delete_item(self, api_key):
        """
        Delete api_key from DynamoDB
        """      
        response = self.table.delete_item(
            Key={
                'api_key':api_key,
            },
            ReturnValues="ALL_OLD"
        )

        return response.get('Attributes')
    
    def get_key_owner(self, api_key):
        """
        Returns the email, project, and agency associated with the api_key
        Returns None if the api_key is not found or is disabled
        """
        params = {
                  'KeyConditionExpression': 'api_key = :api_key',
                  'FilterExpression':"enabled = :enabled",
                  'ExpressionAttributeValues': {
                        ':api_key' : api_key,
                        ':enabled': True
                  },
                  'ProjectionExpression':'email, #p, agency',
                  'ExpressionAttributeNames': {"#p":"project"},
                  }

        items = query_all_items(table=self.table, params=params)

        if not items:
            return None

        return items[0]
    
    def get_all_key_by_email(self, email):
        """
        Returns all api_keys associated with the email
        """
        index_name = self.INDEX_SORT_BY_EMAIL_CREATED

        params = {'IndexName': index_name,
                  'KeyConditionExpression': 'email = :email',
                  'FilterExpression':"enabled = :enabled",
                  'ExpressionAttributeValues': {
                        ':email' : email,
                        ':enabled': True
                  },
                  'ProjectionExpression':'api_key, agency, project, created',
                  }

        items = query_all_items(table=self.table, params=params)

        return get_return_status(item=items, status=HTTPStatus.OK,
                                 message='Successful')
    
    def get_key_by_project(self, project):
        """
        Returns all api_keys associated with the project
        """
        index_name = self.INDEX_SORT_BY_PROJECT

        params = {'IndexName': index_name,
                  'KeyConditionExpression': '#p = :project',
                  'FilterExpression':"enabled = :enabled",
                  'ExpressionAttributeValues': {
                        ':project' : project,
                        ':enabled': True
                  },
                  'ProjectionExpression':'api_key, email, agency, created',
                  'ExpressionAttributeNames': {"#p":"project"},
                  }

        items = query_all_items(table=self.table, params=params)

        return get_return_status(item=items, status=HTTPStatus.OK,
                                 message='Successful')


if __name__ == "__main__":
    dynamodb = boto3.resource("dynamodb", endpoint_url=r"http://localhost:8000/")
    model = ApikeyModel(dynamodb, TABLE_MOONSHOT_APIKEY)

    result = model.get_item("test-api-key")
    print("PUT:", result)
