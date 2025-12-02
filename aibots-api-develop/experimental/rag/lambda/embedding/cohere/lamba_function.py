import boto3
import json

class BedRockEmbedder:
    def __init__(self):
        """Class to generate all 3 responses from OpenAI"""

        self.content_type = 'application/json'

        self.bedrock = boto3.client(service_name='bedrock-runtime')
        self.accept = '*/*'

    def create_embeddings(self, text, model =  'cohere.embed-english-v3'):
        input_type = "search_document"
        body = json.dumps({
            "texts": [
                text,
                ],
            "input_type": input_type}
        )
        response = self.bedrock.invoke_model(
            body=body,
            modelId=model,
            accept=self.accept,
            contentType=self.content_type
        )
        response_body = json.loads(response.get('body').read())
        return response_body['embeddings'][0]
    

def lambda_handler(event, context):

    embedder = BedRockEmbedder()   
    text = event["queryStringParameters"]["text"] #TODO
    event["queryStringParameters"]["embeddings"] = embedder.create_embeddings(text)
    
    return {
        'statusCode': 200,
        'body': json.dumps(event["queryStringParameters"]), #TODO
        'headers': {
            'Content-Type': 'application/json',
        }
    }