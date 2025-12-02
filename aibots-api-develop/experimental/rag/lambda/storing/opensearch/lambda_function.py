from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3

class FileIndexer:
    def __init__(self, host, index_name, embedding_type="cohere"):
        """Upload files"""
        # Initialize index
        self.index_name = index_name
        region = 'ap-southeast-1'  
        service = 'aoss'
        credentials = boto3.Session().get_credentials()
        self.auth = AWSV4SignerAuth(credentials, region, service)
        
        # Intialize dictionary of sizes
        embedding_sizes = {
            "cohere": 1024
        }

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
        
        # Check if index exist, if not, create one
        if not self.client.indices.exists(index = self.index_name):
            settings = {
                "settings": {
                    "index": {
                        "knn": True,
                    }
                },
                "mappings": {
                    "properties": {                       
                        "source": {"type": "text"},
                        "page_number": {"type": "text"},
                        "last_update_date": {"type": "text"},
                        "text": {"type": "text"},
                        "chunk": {"type": "integer"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": embedding_sizes[embedding_type],
                            "method": {
                                "name": "hnsw",
                                "space_type": "innerproduct",
                                "engine": "faiss",
                                    "parameters": {
                                        "ef_construction": 256
                                    }
                            }
                        },
                    }
                },
            }
            self.client.indices.create(index=index_name, body=settings)
 

    def push_to_index(self, documents):
        """
        args:
            documents(list): list of dictionaries of documents
        """
        
        # Iterate and push to index
        for i, doc in enumerate(documents):
            document = {
                "source": doc["metadata"]["source"],
                "page_number": doc["metadata"]["page_number"],
                "last_update_date": doc["metadata"]["last_update_date"],
                "text": doc["text"],
                "chunk": i,
                "embedding": doc["embedding"]
            }
            # add everything to index
            response = self.client.index(
                index = self.index_name, 
                body = document
            )
            return response['result']
            
    def delete_file(self, file_name):
        query = {
            'query': {
                'match': {
                    "file_name": file_name
                    }
                }
            }
        response = self.client.search(index =self.index_name, body =query, version = True)
        file_deleted = None

        id_list = [q['_id'] for q in response['hits']['hits']]
        for id in id_list:

            self.client.delete(
                index = self.index_name,
                id = id
            )
            file_deleted = True
        return file_deleted
    
def lambda_handler(event, context):
    """
    for record in event['Records']:
        # Get the SQS message
        message = json.loads(record['body'])
        
        # Extract bucket name and file key from the message
        bucket_name = message['Records'][0]['s3']['bucket']['name']
        file_key = message['Records'][0]['s3']['object']['key']
    """
        
    document = event["queryStringParameters"]["document"] # TODO: To format based on message structure
    host = event["queryStringParameters"]["host"]
    index_name = event["queryStringParameters"]["index_name"] # TODO: Bot name
    embedding_type = event["queryStringParameters"]["emebdding_type"] # TODO: embedding type

    fileindexer = FileIndexer(host, index_name, embedding_type)
    fileindexer.push_to_index(document)
    
    return {
        'statusCode': 200,
        'body': 'success',
        'headers': {
            'Content-Type': 'application/json',
        }
    }