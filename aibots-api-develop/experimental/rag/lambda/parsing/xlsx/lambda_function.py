import json
import boto3
import pandas as pd
from io import BytesIO

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    try:
        for record in event['Records']:
            # Get the SQS message
            message = json.loads(record['body'])
            
            # Extract bucket name and file key from the message
            bucket_name = message['Records'][0]['s3']['bucket']['name']
            file_key = message['Records'][0]['s3']['object']['key']
            """
            #bucket_name = event["queryStringParameters"]["bucket"]
            #bot = event["queryStringParameters"]["bot"]
            #file_key = bot+"/"+event["queryStringParameters"]["file_key"]
            """
            # Get the file's last modified date
            response = s3_client.head_object(Bucket=bucket_name, Key=file_key)
            last_modified_date = response['LastModified']
            
            # Read the file from S3
            obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
            data = obj['Body'].read().decode('utf-8')
            xls = pd.ExcelFile(BytesIO(data))
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(BytesIO(data), header=0, sheet_name=sheet_name)
                df_json = df.to_dict(orient='records')
                df_json_with_metadata = []
                filename = file_key.split('/')[-1]
                for row in df_json:
                    # Format SQS message
                    df_json_with_metadata.append(
                        {
                        'text': "{" + f'File: {filename}, data: {str(row)}' + "}",
                        "metadata": {
                            "source": filename,
                            "page_number": sheet_name,
                            "last_update_date": last_modified_date.strftime("%Y-%m-%d %H:%M:%S.%f")
                            }
                        }
                    )
        return {
            'statusCode': 200,
            'body': json.dumps(df_json_with_metadata),
            'headers': {
                'Content-Type': 'application/json',
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
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
        
        
        return {
            'statusCode': 200,
            'body': json.dumps(df_json_with_metadata),
            'headers': {
                'Content-Type': 'application/json',
            }
        }
    return {
        'statusCode': 200,
        'body': json.dumps('Messages sent successfully!')
    }
    """