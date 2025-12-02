import json
import boto3

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # try:
    #     for record in event['Records']:
    #         # Get the SQS message
    #         message = json.loads(record['body'])
            
    #         # Extract bucket name and file key from the message
    #         bucket_name = message['Records'][0]['s3']['bucket']['name']
    #         file_key = message['Records'][0]['s3']['object']['key']
    #         last_modified_date = response['LastModified']

    bucket_name = event["queryStringParameters"]["bucket"]
    bot = event["queryStringParameters"]["bot"]
    file_key = bot+"/"+event["queryStringParameters"]["file_key"]

    # Get the file from S3
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    last_modified_date = response['LastModified']
    
    # Read the file's content
    text = response['Body'].read().decode('utf-8')
    df_json_with_metadata= {
        'text': text,
        "metadata": {
            "source": file_key,
            "page_number": 0,
            "last_update_date": last_modified_date.strftime("%Y-%m-%d %H:%M:%S.%f")
        }
    }
    return {
        'statusCode': 200,
        'body': json.dumps([df_json_with_metadata]),
        'headers': {
            'Content-Type': 'application/json',
        }
    }
    # except Exception as e:
    #     return {
    #         'statusCode': 500,
    #         'body': json.dumps({'error': str(e)})
    #     }
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