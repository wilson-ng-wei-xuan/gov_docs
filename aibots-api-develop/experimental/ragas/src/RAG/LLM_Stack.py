import os
import aiohttp

#from dotenv import load_dotenv
#load_dotenv()

class AIBots:
    def __init__(self, bot_name):
        self.user_key = os.getenv("USER_KEY")
        self.bot_name = bot_name
        self.bot_id = None
        
    async def get_bot_id(self):
        url = 'https://bots-api.launchpad.tech.gov.sg/ragas/bot-id'
        params = {
            'bot_name': self.bot_name,
            'user_key': self.user_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                bot = await response.json()

        if len(bot) == 1:
            self.bot_id = bot[0]['id']
        elif len(bot)>1:
            self.bot_id = ";;;Duplicated;;;"
        else:
            self.bot_id = None

    async def chat(self, instruction):
        if self.bot_id == None:
            self.get_bot_id()
            if self.bot_id == None:
                return None
        url = f'https://bots-api.launchpad.tech.gov.sg/ragas/bots/{self.bot_id}/chats?user_key={self.user_key}'
        # Parameters required for the request
        params ={
            "messages": [
                {
                "role": "user",
                "content": instruction
                }
            ],
            "conversation_id": "test",
            "conversation_title": "test",
            "pinned": True,
            "temperature": 0
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params) as response:
                return await response.json()

    def get_context_ans(self, response):
        system_prompt = response['rag_messages'][0]['content']
        answer = response['response']['content']
        split_str = 'You have knowledge of the following information:'
        if split_str in system_prompt:
            context = system_prompt.split(split_str)[1].strip()
        else:
            context = ''
        return context, answer
        

    async def get_chat_history(self, k = 10):
        if self.bot_id == None:
            self.get_bot_id()
            if self.bot_id == None:
                return None
        url = f'https://bots-api.launchpad.tech.gov.sg/ragas/bots/{self.bot_id}/chats?user_key={self.user_key}&limit={k}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response = await response.json()
        conversations = response['conversations']
        return conversations