from openai import OpenAI
from openai import AzureOpenAI
import os

# client = OpenAI()
client = AzureOpenAI()


class BaseNode:
    def __init__(self, node_name, system_prompt = None):
        self.node_name = node_name
        self.chat_history = []
        self.system_prompt = system_prompt
        if self.system_prompt:
            self.chat_history.append({"role": "system", "content": self.system_prompt})        

    def generate(self):
        completion = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=self.chat_history,
            # temperature = 0
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