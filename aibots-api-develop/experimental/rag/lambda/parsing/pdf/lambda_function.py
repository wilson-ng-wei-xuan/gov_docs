import json
import boto3
import io
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title
from langchain_core.documents import Document
import os

s3_client = boto3.client('s3')
def chunk_document(elements, chunk_size):

    elements = chunk_by_title(
        elements,
        new_after_n_chars = chunk_size,
        #overlap = int(chunk_size*.10)
        )
    documents = []
    for element in elements:
        metadata = element.metadata.to_dict()
        del metadata["languages"]
        metadata["source"] = metadata["filename"]
        documents.append(Document(page_content=element.text, metadata=metadata))

    return documents

def docs_to_json(docs, filename = None, last_modified = None):
    cleaned_json_list = []
    for doc in docs:
        page_number = str(doc.metadata["page_number"] if "page_number" in list(doc.metadata.keys()) else "")
        text = "{" + f"File name: {doc.metadata['filename']}, page: {page_number}, content: {doc.page_content}" + "}"
        cleaned_json = {
            'text': text,
            "metadata": {
                "source": doc.metadata['filename'] if 'filename' in doc.metadata else filename,
                "page_number": page_number,
                "last_update_date": last_modified.strftime("%Y-%m-%d %H:%M:%S.%f")
            }
        }
        cleaned_json_list.append(cleaned_json)
    return cleaned_json_list

def lambda_handler(event, context):
    """
    for record in event['Records']:
        # Get the SQS message
        message = json.loads(record['body'])
        
        # Extract bucket name and file key from the message
        bucket_name = message['Records'][0]['s3']['bucket']['name']
        file_key = message['Records'][0]['s3']['object']['key']
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

    elements = partition_pdf(
        filename=local_file_path,        
        pdf_infer_table_structure=True, 
        model_name="yolox"
    )
    
    elements = [el for el in elements if el.category != "Header"]

    documents = chunk_document(elements, chunk_size = chunk_size)
    df_json_with_metadata = docs_to_json(documents, file_key.split('/')[-1], last_modified_date)

    return {
        'statusCode': 200,
        'body': json.dumps(df_json_with_metadata),
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