from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3

class FileIndexer:
    def __init__(self, host, index_name):
        """Upload files"""
        # Initialize index
        self.index_name = index_name
        region = 'ap-southeast-1'  
        service = 'aoss'
        credentials = boto3.Session().get_credentials()
        self.auth = AWSV4SignerAuth(credentials, region, service)


        # create an opensearch client and use the request-signer
        self.client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=self.auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            pool_maxsize=20,
            timeout = 10
        )
    def query(self, query, query_vector, k):
        # Hybrid search
        payload = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "script_score": {
                                "query": {
                                    "match": {
                                        "text": query
                                    }
                                },
                                "script": {
                                    "source": "_score"
                                }
                            }
                        },
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_vector,
                                    "k": k
                                    }
                                }
                        }
                    ]
                }
            }
        }

        docs =  self.client.search(body=payload, index=self.index_name)

        return docs['hits']['hits']
    

def lambda_handler(event, context):
    """
    for record in event['Records']:
        # Get the SQS message
        message = json.loads(record['body'])
        
        # Extract bucket name and file key from the message
        bucket_name = message['Records'][0]['s3']['bucket']['name']
        file_key = message['Records'][0]['s3']['object']['key']
    """
        
    query = event["queryStringParameters"]["query"] # TODO: To format based on message structure
    host = event["queryStringParameters"]["host"]# TODO: To format based on message structure
    index_name = event["queryStringParameters"]["index_name"]# TODO: To format based on message structure
    embedding = event["queryStringParameters"]["embedding"]# TODO: To format based on message structure
    k =  event["queryStringParameters"]["k"]# TODO: To format based on message structure

    fileindexer = FileIndexer(host, index_name)
    fileindexer.query(query, embedding, k)
    
    return {
        'statusCode': 200,
        'body': 'success',
        'headers': {
            'Content-Type': 'application/json',
        }
    }