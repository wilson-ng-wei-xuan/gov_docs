import boto3

bedrock_agent_runtime = boto3.client(
    service_name = "bedrock-agent-runtime"
)
client =  boto3.client('bedrock-agent')

def retrieve(query, kbId, data_source_uri, numberOfResults=5):
    return bedrock_agent_runtime.retrieve(
        retrievalQuery= {
            'text': query
        },
        knowledgeBaseId=kbId,
        retrievalConfiguration= {
            'vectorSearchConfiguration': {
                'numberOfResults': numberOfResults,
                "filter": {
                    "startsWith": {
                        "key": 'x-amz-bedrock-kb-source-uri',
                        "value": data_source_uri
                    }
                }
            }
        }
    )

def get_data_source_id(kbId):
    response = client.list_data_sources(
        knowledgeBaseId=kbId,
    )
    if 'dataSourceSummaries' in response:
        if len(response['dataSourceSummaries'])>0:
            all_sources = response['dataSourceSummaries']
            return [source['dataSourceId'] for source in all_sources]

def get_data_source_uri(kbId, data_source_id):
    response = client.get_data_source(
         dataSourceId=data_source_id,
         knowledgeBaseId=kbId
         )
    source_uri = (
        response['dataSource']['dataSourceConfiguration']['s3Configuration']['bucketArn'].replace('arn:aws:', '').replace(':::', '://')
            + "/"
            + response['dataSource']['dataSourceConfiguration']['s3Configuration']['inclusionPrefixes'][0]
            )
    return source_uri


def start_ingestion_job(kbId, data_source_id):
    response =  client.start_ingestion_job(
        dataSourceId=data_source_id,
        knowledgeBaseId=kbId
    )
    return response['ingestionJob']['ingestionJobId']

def get_ingestion_job_status(kbId, data_source_id, ingestionJobId):
    response =  client.get_ingestion_job(
        dataSourceId = data_source_id,
        ingestionJobId= ingestionJobId,
        knowledgeBaseId= kbId
    )

    return response['ingestionJob']['status']

