from openai import AsyncAzureOpenAI
import os
import asyncio
import random


class ChatCompletor:
    def __init__(self,  model="gpt-4-turbo", emb_model = "text-embedding-ada-002", use_json = False):
        self.model=model
        self.emb_model = emb_model
        self.client = AsyncAzureOpenAI(
            api_key = os.getenv("OPENAI_API_KEY"),  
            api_version = "2023-12-01-preview",
            azure_endpoint = os.getenv("API_BASE")
        )
        self.json = use_json
    async def open_ai_chat_completion(self, 
                                      prompt,
                                      system_prompt =  "You are an expert in evaluating the output of artificial intelligence and machine learning generative models."
                                      ):
        if self.json:
            system_prompt = 'You are a helpful assistant designed to output strictly in JSON. The keys should be TP, FP, FN.'
            response = await self.client.chat.completions.create(
                model=self.model,
                response_format={ "type": "json_object" },
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
            )
        else:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
            )
        await asyncio.sleep(random.uniform(0.01, 0.05))
        return response.choices[0].message.content
    
    async def create_embeddings(self,text):
        text = text.replace("\n", " ")
        response = await self.client.embeddings.create(input=[text], model=self.emb_model)
        return response.data[0].embedding