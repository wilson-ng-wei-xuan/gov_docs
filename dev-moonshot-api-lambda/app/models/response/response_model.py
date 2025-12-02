import logging
import datetime
from uuid import uuid4
from decimal import Decimal
from http import HTTPStatus

import boto3
from boto3.dynamodb import conditions
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from app.config import TABLE_MOONSHOT_LLM, GPT_MODEL_DEFAULT, DATETIME_MS_FORMAT
from app.utils import llm_util
from app.utils.dynamodb_model import DynamodbModel
from app.utils.query_util import (delete_item_handling, get_item_handling,
                                  get_return_status, put_item_handling, query_all_items, scan_all_items,
                                  remove_attributes, update_item_handling)

"""
DynamoDB related functions always return a dictionary containing at least 'HTTPStatusCode' and 'Message'. 
"""

from app.config import logger


class GptResponseModel(DynamodbModel):
    INDEX_SORT_BY_CALLER_CREATED = 'index_llm_caller_created'

    def __init__(self, dynamodb, table_name):
        super().__init__(dynamodb, table_name)
        self.dynamodb = dynamodb
        self.table_name = table_name
        self.table = dynamodb.Table(table_name)
        self.llm_task = 'GPT#prompt'

    def get_item(self, response_id: str):
        response = self.table.get_item(Key={'llm_task':self.llm_task,'id': response_id})

        if not response.get('Item'):
            return None

        return {'Item': response.get('Item')}
                                          
    def put_gpt_response(self, response_id, prompt, model, temperature, response, caller, tokens_used, created):
        """
        Store GPT prompt/model/response and additional params into DynamoDB
        """
        if not response_id:
            response_id = str(uuid4())

        create_time = datetime.datetime.fromtimestamp(created).strftime(DATETIME_MS_FORMAT)

        response = self.table.put_item(
            Item={
                'llm_task':self.llm_task,
                "id": response_id,
                "prompt": prompt,
                "model": model,
                "temperature": Decimal(str(temperature)),
                "response": response,
                "caller": caller,
                "tokens_used": tokens_used,
                "created": create_time,
            },
            ConditionExpression="llm_task <> :llm_task AND id <> :id",
            ExpressionAttributeValues={':llm_task': self.llm_task, ":id": response_id},
        )

        # Get the saved item
        return self.get_item(response_id)

    def mark_emailed(self, response_id):
        response = self.table.get_item(Key={'llm_task':self.llm_task,'id': response_id})
        item = response.get('Item')
        if not item:
            return get_return_status(status=HTTPStatus.NOT_FOUND,
                                         message=f'Item not found: response_id={response_id}')

        response = self.table.update_item(Key={'llm_task':self.llm_task,'id': response_id},
                                              UpdateExpression="set emailed = :emailed",
                                              ExpressionAttributeValues={":emailed":datetime.datetime.now().strftime(DATETIME_MS_FORMAT)},
                                              ReturnValues='ALL_NEW')
        return get_return_status(status=HTTPStatus.OK, message='Update Successful', item=response['Attributes'])
          
    def upvote_response(self, response_id):
        response = self.table.get_item(Key={'llm_task':self.llm_task,'id': response_id})
        item = response.get('Item')
        if not item:
            return get_return_status(status=HTTPStatus.NOT_FOUND,
                                         message=f'Item not found: response_id={response_id}')

        response = self.table.update_item(Key={'llm_task':self.llm_task,'id': response_id},
                                              UpdateExpression="set upvoted = :upvoted",
                                              ExpressionAttributeValues={":upvoted":datetime.datetime.now().strftime(DATETIME_MS_FORMAT)},
                                              ReturnValues='ALL_NEW')
        return get_return_status(status=HTTPStatus.OK, message='Update Successful', item=response['Attributes'])
    
    def downvote_response(self, response_id):
        response = self.table.get_item(Key={'llm_task':self.llm_task,'id': response_id})
        item = response.get('Item')
        if not item:
            return get_return_status(status=HTTPStatus.NOT_FOUND,
                                         message=f'Item not found: response_id={response_id}')

        response = self.table.update_item(Key={'llm_task':self.llm_task,'id': response_id},
                                              UpdateExpression="set downvoted = :downvoted",
                                              ExpressionAttributeValues={":downvoted":datetime.datetime.now().strftime(DATETIME_MS_FORMAT)},
                                              ReturnValues='ALL_NEW')
        return get_return_status(status=HTTPStatus.OK, message='Update Successful', item=response['Attributes'])
    
    def list_tokens_used_by_caller(self, caller: str, past_hours:int = 24,
                                  in_desc: bool = True,
                                  limit: int = 0):
        # List items from database using GSI-PK
        index_name = self.INDEX_SORT_BY_CALLER_CREATED
        cutoff_datetime = (datetime.datetime.now() - datetime.timedelta(hours=past_hours)).strftime(DATETIME_MS_FORMAT)

        params = {'IndexName': index_name,
                  'KeyConditionExpression': 'caller = :caller AND created > :cutoff_datetime',
                  #'FilterExpression':"llm_task = :llm_task",
                  'ExpressionAttributeValues': {
                        #':llm_task': self.llm_task,
                        ':caller': caller,
                        ":cutoff_datetime": cutoff_datetime,
                  },
                  'ProjectionExpression':'created,tokens_used',
                  'ScanIndexForward': not in_desc}

        if limit:
            params['Limit'] = limit

        data = query_all_items(table=self.table, params=params)

        # Need to return empty array if there is no record
        # Because it isn't an error
        return get_return_status(item=data, status=HTTPStatus.OK,
                                 message='Successful')

if __name__ == "__main__":
    dynamodb = boto3.resource("dynamodb", endpoint_url=r"http://localhost:8000/")
    model = GptResponseModel(dynamodb, TABLE_MOONSHOT_LLM)

    prompt = "Say this is a test"

    response = llm_util.gpt_completion(prompt=prompt, model=GPT_MODEL_DEFAULT)
    result = model.put_gpt_response(prompt=prompt, response=response, model=model)
    print("PUT:", result)
