import logging
import datetime
from uuid import uuid4
from decimal import Decimal

import boto3
from boto3.dynamodb import conditions
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from app.config import TABLE_MOONSHOT_LLM, PALM_TEXT_MODEL_DEFAULT, DATETIME_TZ_FORMAT
from app.utils import llm_util
from app.utils.dynamodb_model import DynamodbModel

"""
DynamoDB related functions always return a dictionary containing at least 'HTTPStatusCode' and 'Message'. 
"""

from app.config import logger


class PalmTextModel(DynamodbModel):
    def __init__(self, dynamodb, table_name):
        super().__init__(dynamodb, table_name)
        self.dynamodb = dynamodb
        self.table_name = table_name
        self.table = dynamodb.Table(table_name)
        self.llm_task = 'PALM#text'

    def get_item(self, response_id: str):
        response = self.table.get_item(Key={'llm_task':self.llm_task,'id': response_id})

        if not response.get('Item'):
            return None

        return {'Item': response.get('Item')}
                                          
    def put_text_response(self, response_id, prompt, model, temperature, top_p, top_k, response, caller):
        """
        Store PaLM prompt/model/response and additional params into DynamoDB
        """
        if not response_id:
            response_id = str(uuid4())
        
        create_time = datetime.datetime.utcnow().strftime(DATETIME_TZ_FORMAT)

        response = self.table.put_item(
            Item={
                'llm_task':self.llm_task,
                "id": response_id,
                "prompt": prompt,
                "model": model,
                "temperature": Decimal(str(temperature)),
                "top_p": Decimal(str(top_p)),
                "top_k": Decimal(str(top_k)),
                "response": response,
                "caller": caller,
                "created": create_time,
            },
            ConditionExpression="llm_task <> :llm_task AND id <> :id",
            ExpressionAttributeValues={':llm_task': self.llm_task, ":id": response_id},
        )

        # Get the saved item
        return self.get_item(response_id)



if __name__ == "__main__":
    dynamodb = boto3.resource("dynamodb", endpoint_url=r"http://localhost:8000/")
    model = PalmTextModel(dynamodb, TABLE_MOONSHOT_LLM)

    prompt = "Say this is a test"

    response = llm_util.palm_text(prompt=prompt, model=PALM_TEXT_MODEL_DEFAULT)
    result = model.put_text_response(prompt=prompt, response=response, model=model)
    print("PUT:", result)
