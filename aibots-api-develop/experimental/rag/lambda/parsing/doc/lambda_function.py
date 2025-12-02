import json
import boto3
import io
import os
import logging

s3_client = boto3.client('s3')

from unstructured.partition.docx import partition_docx
from unstructured.chunking.title import chunk_by_title

def chunk_document(elements, chunk_size, last_modified, filename):

    elements = chunk_by_title(
        elements,
        new_after_n_chars = chunk_size,
        #overlap = int(chunk_size*.10)
        )
    cleaned_json_list = []
    for element in elements:
        metadata = element.metadata.to_dict()
        del metadata["languages"]
        metadata["source"] = metadata["filename"]
        #documents.append(Document(page_content=element.text, metadata=metadata))
        page_number = str(metadata["page_number"] if "page_number" in list(metadata.keys()) else "")
        text = "{" + f"File name: {metadata['filename']}, page: {page_number}, content: {element.text}" + "}"
        cleaned_json = {
            'text': text,
            "metadata": {
                "source": metadata['filename'] if 'filename' in metadata else filename,
                "page_number": page_number,
                "last_update_date": last_modified.strftime("%Y-%m-%d %H:%M:%S.%f")
            }
        }
        cleaned_json_list.append(cleaned_json)
    return cleaned_json

def lambda_handler(event, context):
    """
    for record in event['Records']:
        # Get the SQS message
        message = json.loads(record['body'])
        
        # Extract bucket name and file key from the message
        bucket_name = message['Records'][0]['s3']['bucket']['name']
        file_key = message['Records'][0]['s3']['object']['key']
        print(bucket_name, file_key)
        """    


    bucket_name = event["queryStringParameters"]["bucket"]
    bot = event["queryStringParameters"]["bot"]
    file_key = bot+"/"+event["queryStringParameters"]["file_key"]

    chunk_size = event["queryStringParameters"]["chunk_size"] # TODO: Chunk size
    
    # Get the file's last modified date
    response = s3_client.head_object(Bucket=bucket_name, Key=file_key)
    last_modified_date = response['LastModified']
    
    # Define the local file path
    local_file_path = '/tmp/' + os.path.basename(file_key)
    
    # Download the file from S3 to the local file system
    s3_client.download_file(bucket_name, file_key, local_file_path)

    logging.info("Downloaded File.")

    elements = partition_docx(filename=local_file_path)

    logging.info("Partitioned document.")
    
    elements = [el for el in elements if el.category != "Header"]

    num_title = len([el for el in elements if el.category.lower() == "title"])

    if num_title >0:

        documents = chunk_document(elements, chunk_size, last_modified_date, file_key )
    
        return {
            'statusCode': 200,
            'body': json.dumps(documents),
            'headers': {
                'Content-Type': 'application/json',
            }
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps(num_title),
            'headers': {
                'Content-Type': 'application/json',
            }
        }
    """
        for docs in df_json_with_metadata:
            sqs_client = boto3.client('sqs')
            # Send the output message to the next SQS queue
            OUTPUT_SQS_URL = '' ## What is the output SQS?
            sqs_client.send_message(
                QueueUrl=OUTPUT_SQS_URL,
                MessageBody=json.dumps(docs)
            )
        
        for docs in df_json_with_metadata:
            return {
                'statusCode': 200,
                'body': json.dumps(docs),
                'headers': {
                    'Content-Type': 'application/json',
                }
            }
    return {
        'statusCode': 200,
        'body': json.dumps('Messages sent successfully!')
    }
    """