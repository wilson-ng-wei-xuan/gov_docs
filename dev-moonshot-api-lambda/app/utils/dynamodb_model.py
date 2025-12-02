import json
from pathlib import Path
from typing import List, Dict
import logging

from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


class DynamodbModel:

    def __init__(self, dynamodb, table_name):
        self.dynamodb = dynamodb
        self.table_name = table_name
        self.table = dynamodb.Table(table_name)

    @staticmethod
    def serialize_object(obj):
        """
        Serialize an object into DynamoDB format
        E.g. {"processed": "true"} => {'processed': {'S': 'true'}}
        """
        serializer = TypeSerializer()
        return {k: serializer.serialize(v) for k, v in obj.items()}

    @staticmethod
    def deserialize_object(self, obj):
        """
        Deserialize an object from DynamoDB format
        E.g.  {'processed': {'S': 'true'}} => {"processed": "true"}
        """
        deserializer = TypeDeserializer()
        return {k: deserializer.deserialize(v) for k, v in obj.items()}

    def create_table(self, param_file_name=None):
        """
        Create a new dynamodb table. Use parameters in the input file if available.
        """
        params = {}
        if not param_file_name:
            param_file_name = f'{self.table_name}.json'

            with open(Path(__file__).resolve().parent.joinpath(param_file_name)) as f:
                params = json.loads(f.read())

        logger.info(type(params))

        try:
            self.table = self.dynamodb.create_table(**params)
            return self.table
        except Exception as e:
            logger.error(e)
            raise

    def load_into_table(self, items: List[Dict]):
        """
        Load a list of items into dynamodb table
        """
        result = {'success': [], 'failure': []}
        for item in items:
            try:
                self.table.put_item(Item=item)
                result['success'].append(item)
            except Exception as e:
                logger.error(e)
                result['failure'].append(item)
                continue
        return result

    def verify_table(self):
        try:
            self.table.table_status in ('CREATING', 'UPDATING', 'DELETING', 'ACTIVE')
        except ClientError:
            logger.error(f'DynamoDB Table {self.table_name} doesn\'t exist.')
            raise NameError(f'DynamoDB Table {self.table_name} doesn\'t exist.')
