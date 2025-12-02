from http import HTTPStatus
from typing import List, Optional, Union

from app.config import logger
from botocore.exceptions import ClientError

def get_item_handling(func):
    def inner(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
            if not response:
                raise KeyError('Item not found')

            return get_return_status(item=response.get('Item'),
                                     status=HTTPStatus.OK,
                                     message='Get: Successful')
        except KeyError as ex:
            logger.error(ex)
            return get_return_status(status=HTTPStatus.NOT_FOUND,
                                     message=f'Item not found:: arguments ({kwargs})')
        except ClientError as ex:
            logger.error(ex)
            return get_return_status(status=HTTPStatus.INTERNAL_SERVER_ERROR,
                                     message=ex.response['Error']['Message'])

        except Exception as ex:
            logger.error(f'Unknown error: type={type(ex)}, error={str(ex)}')
            return get_return_status(status=HTTPStatus.INTERNAL_SERVER_ERROR,
                                     message=str(ex))

    return inner

def put_item_handling(func):
    def inner(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
            return get_return_status(item=response.get('Item'),
                                     status=HTTPStatus.OK,
                                     message='Put Item Successful')
        except ValueError as ex:
            # for BAD REQUEST error
            logger.exception(ex)
            return get_return_status(status=HTTPStatus.BAD_REQUEST,
                                     message=str(ex))

        except ClientError as ex:
            logger.error(ex)
            if ex.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return get_return_status(status=HTTPStatus.FORBIDDEN,
                                         message=f'Item already exists')

            return get_return_status(status=HTTPStatus.INTERNAL_SERVER_ERROR,
                                     message=f'{ex}')

    return inner

def update_item_handling(func):
    def inner(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
            return get_return_status(item=response.get('Item'),
                                     status=HTTPStatus.OK,
                                     message='Update Item Successful')

        except ValueError as ex:
            logger.exception(ex)
            return get_return_status(status=HTTPStatus.BAD_REQUEST,
                                     message=str(ex))

        except ClientError as ex:
            logger.error(ex)
            if ex.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return get_return_status(status=HTTPStatus.NOT_FOUND,
                                         message=f'Item already existed')

            return get_return_status(status=HTTPStatus.INTERNAL_SERVER_ERROR,
                                     message=f'{ex}')

    return inner

def delete_item_handling(func):
    def inner(*args, **kwargs):
        try:
            func(*args, **kwargs)
            return get_return_status(status=HTTPStatus.OK, message='Delete: Successful')

        except KeyError as ex:
            logger.error(ex)
            return get_return_status(status=HTTPStatus.NOT_FOUND,
                                     message=f'Item not found')
        except ClientError as ex:
            logger.error(ex)
            if ex.response['Error']['Code'] == "ConditionalCheckFailedException":
                return get_return_status(status=HTTPStatus.INTERNAL_SERVER_ERROR,
                                         message=ex.response['Error']['Message'])

            raise

    return inner

def get_return_status(status: HTTPStatus, message: str,
                      item: Union[dict, List[dict]] = None,
                      count: int = None):
    resp = {'HTTPStatusCode': status, 'Message': message}
    item_label = 'Items' if isinstance(item, list) else 'Item'
    if item:
        resp[item_label] = item

    if count is not None:
        resp['Count'] = count

    return resp

def query_all_items(table, params: dict, attr: str = 'Items'):
    try:
        limit = params.get('Limit')
        response = table.query(**params)

        # DynamoDB returns max 1Mb of data, continue to query if LastEvaluatedKey exists
        data = response.get(attr, [])

        while response.get('LastEvaluatedKey'):
            if limit:
                if len(data) >= limit:
                    break
                else:
                    no_item_left = limit - len(data)
                    params['Limit'] = no_item_left

            params['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = table.query(**params)

            if type(data) is list:
                data.extend(response[attr])
            else:
                data = response.get(attr)

        return data
    except Exception as ex:
        logger.error(ex)
        return None

def scan_all_items(table, params: dict, attr: str = 'Items'):
    try:
        limit = params.get('Limit')
        response = table.scan(**params)

        # DynamoDB returns max 1Mb of data, continue to scan if LastEvaluatedKey exists
        data = response.get(attr, [])

        while response.get('LastEvaluatedKey'):
            if limit:
                if len(data) >= limit:
                    break
                else:
                    no_item_left = limit - len(data)
                    params['Limit'] = no_item_left

            params['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = table.scan(**params)

            if type(data) is list:
                data.extend(response[attr])
            else:
                data = response.get(attr)

        return data
    except Exception as ex:
        logger.error(ex)
        return None

def remove_attributes(data: dict, excluded_attributes: set):
    if not excluded_attributes:
        return data

    result = {}
    for k, v in data.items():
        if k not in excluded_attributes:
            result[k] = v

    return result
