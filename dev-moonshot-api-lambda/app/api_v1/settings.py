from boto3.dynamodb import conditions
from fastapi import APIRouter, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import dynamodb, TABLE_WHITESPACE_SETTINGS

router = APIRouter()
security_http_bearer = HTTPBearer()

table_settings = dynamodb.Table(TABLE_WHITESPACE_SETTINGS)
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'


@router.get('/get_apps')
async def get_apps(credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Return list of available apps and their info
    """
    items = []
    try:
        response = table_settings.query(
            KeyConditionExpression=conditions.Key('category').eq('app_info')
        )
        items = response.get('Items', [])
    except Exception as ex:
        print(f'Dynamodb Table not found: {TABLE_WHITESPACE_SETTINGS}')
        print(ex)

    return {"apps": items}
