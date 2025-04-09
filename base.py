from openai import OpenAI, AsyncOpenAI
from openai import AsyncAzureOpenAI, AzureOpenAI
import os
from dotenv import load_dotenv
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import signal
from together import Together
import json

# Load environment variables from .env file
load_dotenv()

# o1_client = OpenAI()

client = OpenAI()
# client_async = AsyncOpenAI()
client_async = None

# client = OpenAI(
#     api_key=os.getenv("GEMINI_API_KEY"),
#     base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
# )

# client = Together()

# client_async = AsyncAzureOpenAI()
# client = AzureOpenAI()

# Calculate cost (update with actual pricing as per OpenAI's documentation)
# 4o cost
input_cost = 2.5
output_cost = 10
# O1 cost
# input_cost = 15
# output_cost = 60

tokens = 1000000

model_name = 'gpt-4o-2024-08-06'

"""
Model Options:
# OpenAI
gpt-4o-2024-08-06
gpt-4-turbo-2024-04-09
o1-2024-12-17

# Together
deepseek-ai/DeepSeek-R1

# Google:
gemini-2.0-flash
"""

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("The operation timed out")

class BaseNode:
    total_cost = 0
    # new counters
    total_generate_calls = 0
    total_async_generate_calls = 0
    # A class-level list of events
    events = []

    def __init__(self, node_name, system_prompt = None):
        self.node_name = node_name
        self.chat_history = []
        self.system_prompt = system_prompt
        if self.system_prompt:
            self.chat_history.append({"role": "system", "content": self.system_prompt})        

    async def async_generate(self):
        # increment class-level function call counter
        BaseNode.total_async_generate_calls += 1
        
        max_retries = 5
        timeout = 350
        for attempt in range(1, max_retries + 1):
            try:
                print(f"node_name: {self.node_name}, Attempt {attempt} of {max_retries}. Cost: {BaseNode.total_cost}, Total Calls: {BaseNode.total_async_generate_calls+BaseNode.total_generate_calls}")
                
                # Set a timeout of 150 seconds for the chat completion
                task = asyncio.create_task(client_async.chat.completions.create(
                    model=model_name,
                    messages=self.chat_history,
                    temperature=0.5
                ))

                # Use asyncio.wait_for to enforce the timeout
                completion = await asyncio.wait_for(task, timeout=timeout)

                # Process the result if the task completes in time
                output = completion.choices[0].message.content
                self.chat_history.append({"role": "assistant", "content": output})
                token_usage = completion.usage  # Typically contains 'prompt_tokens', 'completion_tokens', and 'total_tokens'
                # print(token_usage)
                prompt_tokens = token_usage.prompt_tokens
                completion_tokens = token_usage.completion_tokens
                    
                # Calculate cost (update with actual pricing as per OpenAI's documentation)
                BaseNode.total_cost += (input_cost*prompt_tokens + output_cost*completion_tokens)/tokens
                await asyncio.sleep(2.5)  
                # time.sleep(2.5)
                return output
            
            except asyncio.TimeoutError:
                print(f"Attempt {attempt} timed out after {timeout} seconds. Retrying...")
                # If we've reached the max retries, raise an error
                if attempt == max_retries:
                    raise TimeoutError("Max retries reached. The operation timed out.")

            except Exception as e:
                print(f"Error in generate: {str(e)}")
                # Raise the error if it's not related to timeout or if it's the last attempt
                if attempt == max_retries:
                    raise e
                
            # Wait a short time before retrying to avoid immediate re-execution
            await asyncio.sleep(2)

    def generate(self, o1_bool=False):
        # increment class-level function call counter
        BaseNode.total_generate_calls += 1

        max_retries = 5
        timeout = 350
        def run_completion():
            if o1_bool and 'gemini' not in model_name:
                completion = client.chat.completions.create(
                    model='o1-2024-12-17',
                    messages=self.chat_history,
                    # temperature=0.5
                )
            else:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=self.chat_history,
                    temperature=0.5
                )
            token_usage = completion.usage  # Typically contains 'prompt_tokens', 'completion_tokens', and 'total_tokens'
            # print(token_usage)
            prompt_tokens = token_usage.prompt_tokens
            completion_tokens = token_usage.completion_tokens
                
            # Calculate cost (update with actual pricing as per OpenAI's documentation)
            BaseNode.total_cost += (input_cost*prompt_tokens + output_cost*completion_tokens)/tokens
            if 'deepseek' in model_name:
                return completion.choices[0].message.content.split(r'</think>')[-1]
            else:
                return completion.choices[0].message.content

        for attempt in range(1, max_retries + 1):
            try:
                print(f"node_name: {self.node_name}, Attempt {attempt} of {max_retries}. Cost: {BaseNode.total_cost}, Total Calls: {BaseNode.total_async_generate_calls+BaseNode.total_generate_calls}")
                
                # Use ThreadPoolExecutor to enforce timeout
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(run_completion)
                    output = future.result(timeout=timeout)  # Wait for the result with a timeout

                # If completed successfully, process and return output
                self.chat_history.append({"role": "assistant", "content": output})
                time.sleep(2.5)
                return output

            except TimeoutError:
                print(f"Attempt {attempt} timed out after {timeout} seconds. Retrying...")
                if attempt == max_retries:
                    raise TimeoutError("Max retries reached. The operation timed out.")
            except Exception as e:
                print(f"Error in generate: {str(e)}")
                if attempt == max_retries:
                    raise e

            # Wait briefly before retrying
            time.sleep(2)
        
    
    def setup(self):
        # Needs To be Implemented
        # self.generate()
        raise NotImplementedError("Subclasses must implement process method")

    def communicate(self, query):
        # Needs To be Implemented
        # self.generate()
        raise NotImplementedError("Subclasses must implement process method")


def save_metrics_to_json(accumulator_count=0, filename="framework_metrics.json"):
    """Saves the BaseNode class metrics to a JSON file."""
    data = {
        "total_cost": BaseNode.total_cost,
        "total_calls": BaseNode.total_generate_calls+BaseNode.total_async_generate_calls+accumulator_count,
        "events": BaseNode.events  # list of event dictionaries
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)