import logging
import datetime
from uuid import uuid4
from decimal import Decimal

import boto3
from boto3.dynamodb import conditions
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from app.config import TABLE_MOONSHOT_LLM, GPT_MODEL_DEFAULT, DATETIME_TZ_FORMAT
from app.utils import llm_util
from app.utils.dynamodb_model import DynamodbModel

"""
DynamoDB related functions always return a dictionary containing at least 'HTTPStatusCode' and 'Message'. 
"""

from app.config import logger


class UsageLogModel(DynamodbModel):
    def __init__(self, dynamodb, table_name):
        super().__init__(dynamodb, table_name)
        self.dynamodb = dynamodb
        self.table_name = table_name
        self.table = dynamodb.Table(table_name)

    def get_item(self, task:str, usage_log_id: str):
        usage_log = self.table.get_item(Key={'llm_task':f'LOG#{task}','id': usage_log_id})

        if not usage_log.get('Item'):
            return None

        return {'Item': usage_log.get('Item')}
                                          
    def put_usage_log(self, project, usage, response, caller, agency):
        """
        Store GPT prompt/model/response and additional params into DynamoDB
        """

        llm_task = f'LOG#{project}'
        usage_log_id = f"log-{uuid4().hex}"
        create_time = datetime.datetime.now().strftime(DATETIME_TZ_FORMAT)

        item_dict ={
                'llm_task':llm_task,
                "id": usage_log_id,
                "usage": usage,
                "response": response,
                "caller": caller,
                "agency": agency,
                "created": create_time,
            }
        
        # Add additional fields if they exist
        if usage.get('model'):
            item_dict['model'] = usage.get('model')
        if usage.get('object'):
            item_dict['object'] = usage.get('object')
        if usage.get('usage'):
            item_dict['tokens'] = usage.get('usage').get('total_tokens')
        if usage.get('prompt'):
            item_dict['usage'] = usage.get('prompt')

        usage_log = self.table.put_item(
            Item=item_dict,
            ConditionExpression="llm_task <> :llm_task AND id <> :id",
            ExpressionAttributeValues={':llm_task': llm_task, ":id": usage_log_id},
        )

        # Get the saved item
        return self.get_item(project, usage_log_id)



if __name__ == "__main__":
    dynamodb = boto3.resource("dynamodb", endpoint_url=r"http://localhost:8000/")
    model = UsageLogModel(dynamodb, TABLE_MOONSHOT_LLM)

    result = model.put_usage_log()
    print("PUT:", result)
