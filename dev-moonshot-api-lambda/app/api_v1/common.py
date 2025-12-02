"""
List of common API endpoints
"""

import json
import logging
import os
import traceback
from pathlib import Path
from typing import Optional
from uuid import uuid1

import boto3
from fastapi import (APIRouter, HTTPException, Request, Security, status)
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import AWS_REGION_NAME
from app.utils.auth_util import check_token_permission
from app.utils.file_util import (remove_prefix)
from app.utils.s3_file import extract_s3_zip_file
from app.utils.s3_util import (create_presigned_upload,
                               key_exists_in_bucket)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

router = APIRouter()
security_http_bearer = HTTPBearer()

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
BUCKET_NAME = os.environ.get('BUCKET_NAME_COMMON', '')
TARGET_KEY = os.environ.get('S3_KEY_COMMON', '')

s3_client = boto3.client(service_name='s3', region_name=AWS_REGION_NAME)
sqs_client = boto3.client(service_name='sqs', region_name=AWS_REGION_NAME)
sns_client = boto3.client(service_name='sns', region_name=AWS_REGION_NAME)
lambda_client = boto3.client(service_name='lambda', region_name=AWS_REGION_NAME)


class UnzipS3FileType(BaseModel):
    """
    Pyaload data type for unzip_s3_file() endpoint.
    """
    src_key: str
    target_folder: Optional[str] = TARGET_KEY
    src_bucket: Optional[str] = BUCKET_NAME
    target_bucket: Optional[str] = BUCKET_NAME


@router.get("/get_s3_presigned_url")
async def get_upload_url(request: Request, object_key: str, bucket_name: str,
                         credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    To get a presigned link to upload files to s3 bucket.
    Usage of the resulted presigned link:
        response = requests.post(url=post_url, data=data,
        files={'file': open(r'./Certificates-20211202T063332Z-001.zip', 'rb')})

    :param request: http request object
    :param object_key: path to store the uploaded file
    :param bucket_name: name of the s3 bucket
    :returns: URL and data fields to perform the upload
    :raises HTTPException: raise exception when upload fails
    """
    jwt_data = check_token_permission(credentials.credentials)
    email = jwt_data['email']

    p = Path(email).joinpath(object_key)
    url, post_data = create_presigned_upload(bucket_name, str(p))

    if url and post_data:
        return JSONResponse(content={'url': url,
                                     'data': post_data},
                            status_code=status.HTTP_201_CREATED)
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to generate pre-signed URL")


@router.post("/unzip_s3_file")
async def unzip_s3_file(request: Request, payload: UnzipS3FileType,
                        credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    To unzip a zip file in S3 bucket

    :param request: http request object
    :param payload: Payload containing parameters src_key, target_key, src_bucket, target_bucket
    :returns: URL to perform the upload
    """
    jwt_data = check_token_permission(credentials.credentials)
    email = jwt_data['email']

    p = Path(email)
    full_src_key = str(p.joinpath(payload.src_key))
    full_target_key = str(p.joinpath(payload.target_folder))

    if not key_exists_in_bucket(s3_client, payload.src_bucket, full_src_key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Target object not found: {payload.src_key}")

    try:
        files = extract_s3_zip_file(BUCKET_NAME, str(full_src_key), str(full_target_key))
        files_relative = [remove_prefix(i, f'{email}/') for i in files]

        return JSONResponse(content={'extracted_files': files_relative},
                            status_code=status.HTTP_201_CREATED)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to unzip {payload.src_key}")


