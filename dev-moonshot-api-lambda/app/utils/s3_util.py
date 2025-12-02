import logging
import os
import traceback
import zipfile
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Dict, List, Tuple, Union

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from botocore.exceptions import ClientError

from app.utils.file_util import recursive_glob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def extract_file_from_s3_zip_file(s3_client, bucket_name, key_path, target_file_name):
    """
    Extract a target file from zip file in s3 bucket and return the file object
    """
    response = s3_client.get_object(Bucket=bucket_name, Key=key_path)
    status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    if status == 200:
        logger.info(f"Successful s3.get_object({bucket_name}, {key_path})")
        buffer = BytesIO(response.get("Body").read())
        z = zipfile.ZipFile(buffer)

        # Process each file within the zip
        for filename in z.namelist():
            if filename == target_file_name:
                logger.info(f"Extracting file {filename}")
                return z.open(filename)
    else:
        logger.warning(
            f"Unsuccessful extract file from S3 ({bucket_name}, {key_path})")
        raise Exception(
            f'Unsuccessful extract file from S3 ({bucket_name}, {key_path})')


def upload_file_object_to_bucket(s3_client, file_obj, bucket, object_key, content_type):
    """Upload a file to an S3 bucket
    :param file_obj: File to upload
    :param bucket: Bucket to upload to
    :param object_key: Key of the uploaded object
    :param content_type: Content type of the file
    :return: True if file was uploaded, else False
    """
    # If S3 object_name was not specified, use file_name

    # Upload the file
    try:
        s3_client.upload_fileobj(file_obj, bucket, f"{object_key}", ExtraArgs={
            'ContentType': content_type})
        return True
    except ClientError as ex:
        logging.error(ex)
        return False


def key_exists_in_bucket(s3_client, bucket_name: str, key: str) -> bool:
    """
    Check if a file exists in a bucket
    """
    try:
        obj = s3_client.head_object(
            Bucket=bucket_name,
            Key=key
        )
        logger.info(obj)
        return True
    except Exception as ex:
        logger.error(ex)
        error_msg = (
            f"Error checking file exists: "
            f"{traceback.format_exc()}"
        )
        logger.error(error_msg)
        return False


def get_content_type_size_of_key(s3_client, bucket_name: str, file_path: str) -> Union[Tuple[str, int], None]:
    """
    Check if a file exists in a bucket
    """
    try:
        obj = s3_client.head_object(
            Bucket=bucket_name,
            Key=file_path
        )
        return obj['ContentType'], obj['ContentLength']
    except Exception as e:
        logging.error(e)
        error_msg = (
            f"Error checking file exists: "
            f"{str(e)}: {traceback.format_exc()}"
        )
        return None


def key_prefix_exists_in_bucket(s3_client, bucket_name: str, key_prefix: str) -> bool:
    """
    Check if a key, which can be a wildcard, exists in a bucket
    Args:
        key_prefix: key in the format of 's3://bucket_name/key_value'
    Return:
        Boolean value on whether a key exists or not
    """
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=key_prefix
        )
        objects = response.get('Contents', [])
        return bool(objects)
    except Exception as e:
        logging.error(e)
        error_msg = (
            f"Error checking key prefix: {key_prefix}"
            f"{str(e)}: {traceback.format_exc()}"
        )
        return False


def download_file_object_from_bucket(s3_client, bucket_name: str, key: str):
    """
    Return a file object from a bucket matching a key
    """
    try:
        # Download from s3
        s3_obj = s3_client.get_object(
            Bucket=bucket_name,
            Key=key
        )
        return s3_obj
    except Exception as e:
        logging.error(e)
        return None


def list_files_in_bucket(s3_client, bucket_name: str, key_prefix: str) -> List[str]:
    """
    List files in a bucket which match prefix
    """
    result = []
    try:
        for obj in s3_client.list_objects_v2(Bucket=bucket_name, Prefix=key_prefix)['Contents']:
            response = get_content_type_size_of_key(
                s3_client, bucket_name, obj['Key'])
            if response and response[1] > 0:
                result.append(obj['Key'])

        return result
    except KeyError as ex:
        logger.exception(str(ex))
    except Exception as ex:
        logger.exception(str(ex))

    return result


def download_folder_from_bucket(s3_client, s3_resource, prefix, bucket_name='your_bucket', local='/tmp'):
    """
    Usage:
        s3_client = boto3.client('s3')
        s3_resource = boto3.resource('s3')
        s3_download_folder(s3_client, s3_resource, 'newsletter/2021-01-01/', 'my-bucket', '/tmp')
    """
    paginator = s3_client.get_paginator('list_objects')
    for page in paginator.paginate(Bucket=bucket_name, Delimiter='/', Prefix=prefix):
        if page.get('CommonPrefixes') is not None:
            for subdir in page.get('CommonPrefixes'):
                download_folder_from_bucket(s3_client, s3_resource, subdir.get(
                    'Prefix'), bucket_name, local)
        for file in page.get('Contents', []):
            dest_pathname = os.path.join(local, file.get('Key'))
            if not os.path.exists(os.path.dirname(dest_pathname)):
                os.makedirs(os.path.dirname(dest_pathname))
            try:
                s3_resource.meta.client.download_file(
                    bucket_name, file.get('Key'), dest_pathname)
            except Exception as ex:
                logger.info(ex)


def upload_file_to_bucket(s3_client, file_path: str, bucket_name: str, object_key: str = None,
                          config: TransferConfig = None):
    """
    Upload a local file to an S3 bucket.

    :param file_path: File to upload
    :param bucket_name: Bucket to upload to
    :param object_key: S3 object name including prefix. If not specified then file_name is used
    :param config: The transfer configuration to be used when performing the transfer.
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_key is None:
        object_key = file_path

    try:
        s3_client.upload_file(
            Filename=file_path, Bucket=bucket_name, Key=object_key, Config=config)
        return True
    except ClientError as e:
        logger.error(e)
        return False


def upload_folder_content_to_bucket(s3_client, local_folder: str, bucket_name: str = 'your_bucket', s3_path: str = ''):
    """
    Upload content in a local folder to S3 bucket
    """
    file_paths = recursive_glob(local_folder)
    logger.info(file_paths)
    config = TransferConfig(multipart_threshold=1024 * 25,
                            max_concurrency=10,
                            multipart_chunksize=1024 * 25,
                            use_threads=True)

    success = []
    failed = []
    for file_path in file_paths:
        logger.info('Uploading {}'.format(file_path))
        object_key = PurePosixPath(Path(s3_path)).joinpath(
            Path(file_path).as_posix())
        status = upload_file_to_bucket(s3_client, os.path.join(local_folder, file_path), bucket_name,
                                       object_key=str(object_key), config=config)
        if status:
            success.append(str(object_key))
        else:
            failed.append(str(object_key))

    return success, failed


def create_presigned_download(s3_client, bucket_name, object_key, expiry=3600):
    """
    Generate a presigned S3 POST URL to download file
    """
    try:
        link = s3_client.generate_presigned_url('get_object',
                                                Params={'Bucket': bucket_name,
                                                        'Key': object_key},
                                                ExpiresIn=expiry)
        return link
    except ClientError as e:
        logger.error(e)


def create_presigned_upload(bucket_name, object_key, expiry=3600):
    """
    Generate a presigned S3 POST URL to upload file
    """
    s3_client = boto3.client('s3', config=Config(signature_version='s3v4'))
    try:
        response = s3_client.generate_presigned_post(Bucket=bucket_name,
                                                     Key=object_key,
                                                     ExpiresIn=expiry)
        url = response['url']
        post_data = response['fields']
        return url, post_data
    except ClientError as ex:
        logger.error(ex)
    return None, None


def read_s3_files_content(s3_client, bucket_name: str, key_path: str) -> Dict:
    """Read the content of all files which matched key_path in a S3 Bucket.
    It returns the content in a dictionary with key_path as key. 
    """
    response = s3_client.list_objects(Bucket=bucket_name, Prefix=key_path)
    result = {}
    for o in response.get('Contents'):
        data = s3_client.get_object(Bucket=bucket_name, Key=o.get('Key'))
        contents = data['Body'].read()
        result[o.get('Key')] = contents.decode("utf-8")
    return result


def folder_exists_in_bucket_and_not_empty(s3_client, bucket_name: str, key: str) -> bool:
    """
    Folder exists and must contain at least 1 file directly. Files in subfolder is not counted. 
    """
    if not key.endswith('/'):
        key += '/'
    resp = s3_client.list_objects(
        Bucket=bucket_name, Prefix=key, Delimiter='/', MaxKeys=1)
    return 'Contents' in resp


def folder_exists_in_bucket(s3_client, bucket_name: str, key: str) -> bool:
    """
    Folder should exists. It could be empty.
    """
    key = key.rstrip('/')
    resp = s3_client.list_objects(
        Bucket=bucket_name, Prefix=key, Delimiter='/', MaxKeys=1)
    return 'CommonPrefixes' in resp


def read_file_from_bucket(s3_client, bucket_name: str, key: str):
    """
    Read content of a file from s3 bucket.
    """
    data = s3_client.get_object(Bucket=bucket_name, Key=key)
    contents = data['Body'].read()
    return contents.decode("utf-8")


def delete_file_from_bucket(s3_client, bucket_name: str, key: str):
    """
    Delete file from bucket
    """
    s3_client.delete_object(Bucket=bucket_name, Key=key)

    
def copy_s3_folder(old_prefix, new_prefix, old_bucket_name, new_bucket_name=None):
    """
    Copy objects matching one prefix to another location in s3 buckets.
    if new_bucket_name is None, copy to the same
    """
    if new_bucket_name is None:
        new_bucket_name = old_bucket_name
    if new_bucket_name == old_bucket_name and new_prefix == old_prefix:
        # Same location, no copy required
        return None

    s3 = boto3.resource('s3')
    old_bucket = s3.Bucket(old_bucket_name)
    new_bucket = s3.Bucket(new_bucket_name)

    for obj in old_bucket.objects.filter(Prefix=old_prefix):
        old_source = {'Bucket': old_bucket_name,
                      'Key': obj.key}
        # replace the prefix
        new_key = new_prefix + obj.key[len(old_prefix):]
        new_obj = new_bucket.Object(new_key)
        new_obj.copy(old_source)


if __name__ == "__main__":
    s3_client = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    S3_BUCKET = 'moonshot-305326993135'
    S3_KEY = 'pdf'
    S3_FOLDER = 'newsletter'

    result = list_files_in_bucket(s3_client, S3_BUCKET, S3_KEY)
    print(result)

    result = key_exists_in_bucket(
        s3_client, 'blastoise-305326993135', 'test')
    logger.info(result)

    result = folder_exists_in_bucket(
        s3_client, 'blastoise-305326993135', 'mark.qj@gmail.com/')
    logger.info(result)

    result = folder_exists_in_bucket_and_not_empty(
        s3_client, 'blastoise-305326993135', 'mark.qj@gmail.com/')
    logger.info(result)

    # #####
    # Test Upload a File

    # file_name = os.path.join('..', 'newsletter', '2021-01-02', 'raw.json')
    # upload_file(s3_client, file_name, S3_BUCKET, os.path.relpath(file_name, '..'))

    # #####
    # Test Upload a Folder

    # upload_folder_content_to_bucket(s3_client, os.path.join(
    #     '../../data', 'newsletter'), S3_BUCKET, 'temp')

    # #####
    # Test Download a Folder

    # newsletter_date = '2021-01-01'
    # TMP_FOLDER = Path.cwd()
    #
    # # Get Paths
    # template_folder = os.path.join(Path.cwd(), f'app/newsletter/template')
    # data_folder = os.path.join(TMP_FOLDER, S3_FOLDER, newsletter_date)
    # data_file = os.path.join(data_folder, 'data.json')
    # Path(data_folder).mkdir(parents=True, exist_ok=True)
    #
    # # Fetch data_folder of newsletter_date from S3 Bucket to /tmp folder
    # bucket_name = S3_BUCKET
    # download_folder(s3_client, s3_resource, f'{S3_FOLDER}/{newsletter_date}/', bucket_name, TMP_FOLDER)
