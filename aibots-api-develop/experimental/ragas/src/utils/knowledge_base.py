import os
import aiohttp

from dotenv import load_dotenv
load_dotenv()

class KnowledgeBase:
    def __init__(self, bot_id):
        self.user_key = os.getenv("USER_KEY")
        self.bot_id = bot_id
        self.kb_id = None
        self.latest_bot_date = None

    async def get_kb_id(self):
        url = f'https://bots-api.launchpad.tech.gov.sg/ragas/bots/{self.bot_id}'
        params = {
            'user_key': self.user_key
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response = await response.json()
        
        if "update" in response['modifications'].keys():
            if "knowledge_bases" in response['modifications']["update"]["details"]:
                self.latest_bot_date = response['modifications']["update"]["timestamp"][:-6]
                self.base_id = response['modifications']["update"]["details"]["knowledge_bases"]
            else:
                self.latest_bot_date = response['modifications']["create"]["timestamp"][:-6]
                self.base_id = response['modifications']["create"]["details"]["knowledge_bases"]
        else:
            self.latest_bot_date = response['modifications']["create"]["timestamp"][:-6]
            self.base_id = response['modifications']["create"]["details"]["knowledge_bases"]

    async def get_latest_date(self):
        if self.latest_bot_date == None:
            await self.get_kb_id()
        if (self.base_id != None) and (self.base_id!='null'):
            url = f'https://bots-api.launchpad.tech.gov.sg/ragas/bases/{self.base_id}'
            params = {
                'user_key': self.user_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    response = await response.json()
            latest_base_date = response['modifications']["update"]["timestamp"][:-6]
            return max(latest_base_date, self.latest_bot_date)
            
        else:
            return self.latest_bot_date