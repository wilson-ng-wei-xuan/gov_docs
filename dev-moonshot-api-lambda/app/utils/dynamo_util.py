import json
import logging
from typing import List, Dict

import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class DynamoTable:

    def __init__(self, table_name):
        self.table_name = table_name
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    @staticmethod
    def create_table(dynamodb: boto3.resource, table_defs: Dict) -> None:
        """
        Create a table in dynamodb using definition in Dictionary
        """
        table_name = table_defs["TableName"]
        logger.info(f'Delete existing table {table_name}')
        DynamoTable.delete_table(dynamodb, table_name)
        logger.info(f'Create table {table_name}')
        table = dynamodb.create_table(**table_defs)

    @staticmethod
    def create_table_from_file(dynamodb: boto3.resource, table_definition_path: str) -> None:
        """
        Create a table in dynamodb using definition JSON file
        """
        with open(table_definition_path) as f:
            table_defs = json.load(f)

        DynamoTable.create_table(dynamodb, table_defs)

    @staticmethod
    def delete_table(dynamodb: boto3.resource, table_name: str) -> None:
        try:
            table = dynamodb.Table(table_name)
            table.delete()
        except Exception as e:
            pass

    def get_item(self, key: Dict) -> Dict:
        try:
            response = self.table.get_item(Key=key)
        except ClientError as e:
            logger.error(e.response['Error']['Message'])
            logger.exception(e)
        else:
            return response['Item']

    def query_table(self, key=None, value=None):
        # try:
        if key is not None and value is not None:
            filtering_exp = Key(key).eq(value)
            response = self.table.query(KeyConditionExpression=filtering_exp)
            return response['Items']

        raise ValueError('Parameters missing or invalid')
        # except Exception as e:
        #     logger.exception(e)
        #     raise Exception(f"Failed to query dynamoDB: {key}:{value}")

    @staticmethod
    def truncate_table(dynamodb: boto3.resource, table_name: str) -> int:
        table = dynamodb.Table(table_name)

        # get the table keys
        tableKeyNames = [key.get("AttributeName") for key in table.key_schema]

        # Only retrieve the keys for each item in the table (minimize setup transfer)
        projectionExpression = ", ".join('#' + key for key in tableKeyNames)
        expressionAttrNames = {'#' + key: key for key in tableKeyNames}

        counter = 0
        page = table.scan(ProjectionExpression=projectionExpression,
                          ExpressionAttributeNames=expressionAttrNames)
        with table.batch_writer() as batch:
            while page["Count"] > 0:
                counter += page["Count"]
                # Delete items in batches
                for itemKeys in page["Items"]:
                    batch.delete_item(Key=itemKeys)
                # Fetch the next page
                if 'LastEvaluatedKey' in page:
                    page = table.scan(
                        ProjectionExpression=projectionExpression, ExpressionAttributeNames=expressionAttrNames,
                        ExclusiveStartKey=page['LastEvaluatedKey'])
                else:
                    break

        logger.info(f"Deleted {counter} items in table {table_name}")
        return counter

    def insert_item(self, item: Dict) -> bool:
        """
        Insert a item into a dynamodb table by table_name
        """
        try:
            self.table.put_item(Item=item)
            return True
        except Exception as e:
            logger.exception(e)
            return False

    def insert_items(self, items: List[Dict]) -> Dict:
        """
        Insert a list of items into a dynamodb table by table_name
        """
        loaded_count = 0
        failed_count = 0
        for item in items:
            try:
                self.table.put_item(Item=item)
                loaded_count += 1
            except Exception as ex:
                logger.error(f'Failed to put_item: {item}')
                logger.exception(ex)
                failed_count += 1

        return {'loaded_count': loaded_count, 'failed_count': failed_count}

    @staticmethod
    def deserialize_dynamodb_event(event: Dict) -> List[Dict]:
        """
        Parse DynamoDB event into a list of dictionary,
            which contains eventName, Keys and NewImage of each record
        """
        deserializer = TypeDeserializer()
        tuple_with_types = [(
            r['eventName'],
            r["dynamodb"]["Keys"],
            r["dynamodb"].get("NewImage", {}),
            r["dynamodb"].get("OldImage", {})) for r in event['Records']]
        data = [{
            'eventName': name,
            'keys': deserializer.deserialize({"M": keys}),
            'newImage': deserializer.deserialize({"M": newImage}),
            'oldImage': deserializer.deserialize({"M": oldImage})
        } for name, keys, newImage, oldImage in tuple_with_types]
        return data

    @staticmethod
    def serialize_object(obj):
        """
        Serialize an object into DynamoDB format
        E.g. {"processed": "true"} => {'processed': {'S': 'true'}}
        """
        serializer = TypeSerializer()
        return {k: serializer.serialize(v) for k, v in obj.items()}

    @staticmethod
    def deserialize_object(obj):
        """
        Deserialize an object from DynamoDB format
        E.g.  {'processed': {'S': 'true'}} => {"processed": "true"}
        """
        deserializer = TypeDeserializer()
        return {k: deserializer.deserialize(v) for k, v in obj.items()}


if __name__ == '__main__':
    # result = DynamoTable.serialize_object({'hello': 'world'})
    # print(result)
    # result = DynamoTable.deserialize_object({'hello': {"S": 'world'}})
    # print(result)

    dynamo_table = DynamoTable('mail_postman')
    result = dynamo_table.query_table('group_task', '20211129142538_048893f9adee38127745fc3f41a3fdc1')
    print(result)

# def create_table(dynamodb: boto3.resource, table_definition_path: str) -> None:
#     """
#     Create a table in dynanodb using definition JSON file
#     """
#     with open(table_definition_path) as f:
#         table_defs = json.load(f)
#
#         table_name = table_defs["TableName"]
#         print(f'Delete existing table {table_name}')
#         delete_table(dynamodb, table_name)
#         print(f'Create table {table_name}')
#         table = dynamodb.create_table(**table_defs)
#
#
# def delete_table(dynamodb: boto3.resource, table_name: str) -> None:
#     try:
#         table = dynamodb.Table(table_name)
#         table.delete()
#     except Exception as e:
#         pass
#
#
# def get_item(dynamodb: boto3.resource, table_name: str, key: Dict) -> Dict:
#     table = dynamodb.Table(table_name)
#     try:
#         response = table.get_item(Key=key)
#     except ClientError as e:
#         print(e.response['Error']['Message'])
#     else:
#         return response['Item']
#
#
# def truncate_table(dynamodb: boto3.resource, table_name: str) -> int:
#     table = dynamodb.Table(table_name)
#
#     # get the table keys
#     tableKeyNames = [key.get("AttributeName") for key in table.key_schema]
#
#     # Only retrieve the keys for each item in the table (minimize setup transfer)
#     projectionExpression = ", ".join('#' + key for key in tableKeyNames)
#     expressionAttrNames = {'#' + key: key for key in tableKeyNames}
#
#     counter = 0
#     page = table.scan(ProjectionExpression=projectionExpression,
#                       ExpressionAttributeNames=expressionAttrNames)
#     with table.batch_writer() as batch:
#         while page["Count"] > 0:
#             counter += page["Count"]
#             # Delete items in batches
#             for itemKeys in page["Items"]:
#                 batch.delete_item(Key=itemKeys)
#             # Fetch the next page
#             if 'LastEvaluatedKey' in page:
#                 page = table.scan(
#                     ProjectionExpression=projectionExpression, ExpressionAttributeNames=expressionAttrNames,
#                     ExclusiveStartKey=page['LastEvaluatedKey'])
#             else:
#                 break
#
#     print(f"Deleted {counter} items in table {table_name}")
#     return counter
#
#
# def insert_items(dynamodb: boto3.resource, table_name: str, items: List[Dict]) -> Dict:
#     """
#     Insert a list of items into a dynamodb table by table_name
#     """
#     table = dynamodb.Table(table_name)
#     loaded_count = 0
#     failed_count = 0
#     for item in items:
#         try:
#             table.put_item(Item=item)
#             loaded_count += 1
#         except Exception as ex:
#             print(f'Failed to put_item: {item}')
#             print(ex)
#             failed_count += 1
#
#     return {'loaded_count': loaded_count, 'failed_count': failed_count}
#
#
# def deserialize_dynamodb_event(event: Dict) -> List[Dict]:
#     """
#     Parse DynamoDB event into a list of dictionary,
#         which contains eventName, Keys and NewImage of each record
#     """
#     deserializer = TypeDeserializer()
#     tuple_with_types = [(
#         r['eventName'],
#         r["dynamodb"]["Keys"],
#         r["dynamodb"].get("NewImage", {}),
#         r["dynamodb"].get("OldImage", {})) for r in event['Records']]
#     data = [{
#         'eventName': name,
#         'keys': deserializer.deserialize({"M": keys}),
#         'newImage': deserializer.deserialize({"M": newImage}),
#         'oldImage': deserializer.deserialize({"M": oldImage})
#     } for name, keys, newImage, oldImage in tuple_with_types]
#     return data
#
#
# def serialize_object(obj):
#     """
#     Serialize an object into DynamoDB format
#     E.g. {"processed": "true"} => {'processed': {'S': 'true'}}
#     """
#     serializer = TypeSerializer()
#     return {k: serializer.serialize(v) for k, v in obj.items()}
#
#
# def deserialize_object(obj):
#     """
#     Deserialize an object from DynamoDB format
#     E.g.  {'processed': {'S': 'true'}} => {"processed": "true"}
#     """
#     deserializer = TypeDeserializer()
#     return {k: deserializer.deserialize(v) for k, v in obj.items()}
#
#
# if __name__ == '__main__':
#     result = serialize_object({'hello': 'world'})
#     print(result)
#     result = deserialize_object({'hello': {"S": 'world'}})
#     print(result)
