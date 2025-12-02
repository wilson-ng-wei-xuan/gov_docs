import logging
import datetime
from uuid import uuid4
from decimal import Decimal

import boto3
from boto3.dynamodb import conditions
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from app.config import TABLE_MOONSHOT_LLM, GPT_MODEL_DEFAULT, DATETIME_MS_FORMAT
from app.utils import llm_util
from app.utils.dynamodb_model import DynamodbModel

"""
DynamoDB related functions always return a dictionary containing at least 'HTTPStatusCode' and 'Message'. 
"""

from app.config import logger


class GptSummaryModel(DynamodbModel):
    def __init__(self, dynamodb, table_name):
        super().__init__(dynamodb, table_name)
        self.dynamodb = dynamodb
        self.table_name = table_name
        self.table = dynamodb.Table(table_name)
        self.llm_task = 'GPT#summarize'

    def get_item(self, summary_id: str):
        summary = self.table.get_item(Key={'llm_task':self.llm_task,'id': summary_id})

        if not summary.get('Item'):
            return None

        return {'Item': summary.get('Item')}
                                          
    def put_gpt_summary(self, summary_id, prompt, model, temperature, summary, caller, tokens_used, created):
        """
        Store GPT prompt/model/response and additional params into DynamoDB
        """
        if not summary_id:
            summary_id = str(uuid4())

        create_time = datetime.datetime.fromtimestamp(created).strftime(DATETIME_MS_FORMAT)

        summary = self.table.put_item(
            Item={
                'llm_task':self.llm_task,
                "id": summary_id,
                "prompt": prompt,
                "model": model,
                "temperature": Decimal(str(temperature)),
                "summary": summary,
                "caller": caller,
                "tokens_used": tokens_used,
                "created": create_time,
            },
            ConditionExpression="llm_task <> :llm_task AND id <> :id",
            ExpressionAttributeValues={':llm_task': self.llm_task, ":id": summary_id},
        )

        # Get the saved item
        return self.get_item(summary_id)



if __name__ == "__main__":
    dynamodb = boto3.resource("dynamodb", endpoint_url=r"http://localhost:8000/")
    model = GptSummaryModel(dynamodb, TABLE_MOONSHOT_LLM)

    text = "Say this is a test"

    response = llm_util.gpt_completion(prompt=text, model=GPT_MODEL_DEFAULT)
    result = model.put_gpt_summary(prompt=text, response=response, model=model)
    print("PUT:", result)
