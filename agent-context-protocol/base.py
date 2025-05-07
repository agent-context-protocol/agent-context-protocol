from openai import OpenAI, AsyncOpenAI
import os
import asyncio
from datetime import datetime

# Load environment variables from .env file
client = OpenAI()
client_async = AsyncOpenAI()
"""
Model Options:
gpt-4o-2024-08-06
o1-2024-12-17
gpt-4.1-2025-04-14
"""

model_name = "gpt-4.1-2025-04-14"


class BaseNode:
    def __init__(self, node_name, system_prompt = None):
        self.node_name = node_name
        self.chat_history = []
        self.system_prompt = system_prompt
        self.date_str = datetime.now().strftime("%b %d, %Y")
        if self.system_prompt:
            self.chat_history.append({"role": "system", "content": self.system_prompt})        

    async def async_generate(self, o1_bool=False):
        self.chat_history.append({"role": "system", "content": f"Btw, Today The Date is: {self.date_str}"}) 
        try:
            if "o1" in model_name or o1_bool:
                task = asyncio.create_task(client_async.chat.completions.create(
                    model="o1-2024-12-17",
                    messages=self.chat_history,
                ))
            else:
                task = asyncio.create_task(client_async.chat.completions.create(
                    model=model_name,
                    messages=self.chat_history,
                    temperature=0
                ))

            completion = await task

            output = completion.choices[0].message.content
            self.chat_history.append({"role": "assistant", "content": output})
            return output
        except Exception as e:
            print(f"Error in generate: {str(e)}")
            raise

    def generate(self, o1_bool=False):
        self.chat_history.append({"role": "system", "content": f"Btw, Today The Date is: {self.date_str}"}) 
        if "o1" in model_name or o1_bool:
            completion = client.chat.completions.create(
                model="o1-2024-12-17",
                messages=self.chat_history,
            )
        else:
            completion = client.chat.completions.create(
                model=model_name,
                messages=self.chat_history,
                temperature = 0
            )
        output = completion.choices[0].message.content
        self.chat_history.append({"role": "assistant", "content": output})
        return output
    
    def setup(self):
        # Needs To be Implemented
        # self.generate()
        raise NotImplementedError("Subclasses must implement process method")

    def communicate(self, query):
        # Needs To be Implemented
        # self.generate()
        raise NotImplementedError("Subclasses must implement process method")