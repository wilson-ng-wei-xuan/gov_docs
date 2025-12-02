import openai
from openai import AsyncAzureOpenAI
import os
import asyncio
import numpy as np
#from dotenv import load_dotenv
#load_dotenv()

class ChatGenerator:
    def __init__(self):
        """Class to generate all 3 responses from OpenAI"""
        openai.api_type = 'azure'
        openai.api_base =  os.getenv("API_BASE")  or 'API_BASE'
        openai.api_version = "2023-03-15-preview"
        openai.api_key =  os.getenv("OPENAI_API_KEY") or 'OPENAI_API_KEY'
        self.client = AsyncAzureOpenAI(
            api_key = os.getenv("OPENAI_API_KEY"),
            base_url = os.getenv("API_BASE")  
            #api_version = "2023-12-01-preview",
            #azure_endpoint = os.getenv("API_BASE")        
        )

    async def chat(self, system_prompt, text_template, model = 'gpt-3.5-turbo'):
        # System prompt

        message = [{"role": "system", "content" :system_prompt}]
        message +=[{"role": "user", "content" : text_template}]

        # Directly use chat completion. No convo memory is stored
        response = await self.client.chat.completions.create(
            temperature = 0.0,
            model= model, 
            messages = message
        )
        
        # Pause to enable prevent overloading API service
        await asyncio.sleep(0.5 + np.random.uniform(low=0.0, high=0.3))
        return response.choices[0].message.content