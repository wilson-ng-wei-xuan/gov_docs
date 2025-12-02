import openai
import os
#import asyncio
import numpy as np
#from dotenv import load_dotenv
#load_dotenv()
import time
import boto3
import json

class OpenAIEmbedder:
    def __init__(self):
        from openai import OpenAI

        """Class to generate all 3 responses from OpenAI"""
        openai.api_type = 'azure'
        openai.api_base =  os.getenv("OPENAI_API_BASE")  or 'OPENAI_API_BASE'
        openai.api_version = "2023-03-15-preview"
        openai.api_key =  os.getenv("OPENAI_API_KEY") or 'OPENAI_API_KEY'
        self.client = OpenAI(
            api_key = os.getenv("OPENAI_API_KEY"),
            base_url = os.getenv("OPENAI_API_BASE")  
            #api_version = "2023-12-01-preview",
            #azure_endpoint = os.getenv("API_BASE")        
        )

    def create_embeddings(self, text, model = 'text-embedding-3-small'):
        text = text.replace("\n", " ")
        # System prompt
        time.sleep(1.0)
        return self.client.embeddings.create(input = [text], model=model).data[0].embedding

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