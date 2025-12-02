
from langchain.text_splitter import RecursiveCharacterTextSplitter
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from src.openai.completor import ChatCompletor

class ExampleRAG:
    def __init__(self):
        self.completor = ChatCompletor()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
            )
        self.all_chunks = []
        self.all_emebddings = []
        self.context = None

    async def encode_docs(self, docs):
        for doc in docs:
            chunks = self.text_splitter.split_text(text=doc)
            for chunk in chunks:
                self.all_emebddings.append(await self.completor.create_embeddings(chunk))
                self.all_chunks.append(chunk)
        self.all_emebddings = np.array(self.all_emebddings)
    
    async def top_k_sim(self, instruction, docs):
        if len(self.all_emebddings)==0:
            await self.encode_docs(docs)
        question_embed = await self.completor.create_embeddings(instruction)
        similarities = cosine_similarity(np.array(question_embed).reshape(1,-1), self.all_emebddings)
        return np.argsort(-similarities)[:3]
    
    def generate_system_prompt(self, personality, functionality, guardrails):
        output_string = f"""You are a personal AI assistant with the personality: {personality}.\n\n
                            Your purpose is: {functionality}.\n\n
                            You must abide by the following rules: {guardrails}.\n\n
                            You have knowledge of the following information: {self.context}"""
        return output_string
    
    async def augment(self, docs, instruction, function):
        if self.context == None:
            rel_index = await self.top_k_sim(instruction, docs)
            self.context = ' '.join([self.all_chunks[i] for i in rel_index[0]] )
        
        personality = "helpful, clever, and very friendly"
        guardrails = "You will not answer politically sensitive topics"
        system_prompt = self.generate_system_prompt(personality, function, guardrails)
        response = await self.completor.open_ai_chat_completion(
            prompt = instruction, 
            system_prompt = system_prompt
        )

        return response
