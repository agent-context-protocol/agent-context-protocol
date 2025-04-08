from openai import OpenAI
import pandas as pd
from tqdm import tqdm
import re
from PIL import Image
import requests
from io import BytesIO
import matplotlib.pyplot as plt
import glob
import os


# EXTERNAL API FUNCTIONS

# We are defining the function which will give us the response from the external api by selecting the right api based on external_api_choice
def perplexity_api_response(dict_body):

    response_dict = {}

    # if True or "query" not in dict_body and "preplexity_ai_key" not in dict_body:
    if "query" not in dict_body and "preplexity_ai_key" not in dict_body:
        response_dict["status_code"] = 400
        response_dict["text"] = "Missing required parameters query and preplexity_ai_key"
        return response_dict
    elif "query" not in dict_body:
        response_dict["status_code"] = 400
        response_dict["text"] = "Missing required parameters query"
        return response_dict
    elif "preplexity_ai_key" not in dict_body:
        response_dict["status_code"] = 400
        response_dict["text"] = "Missing required parameters preplexity_ai_key"
        return response_dict

    query = dict_body["query"]
    preplexity_ai_key = dict_body["preplexity_ai_key"]

    messages = [
        {
            "role": "system",
            "content": "You are an artificial intelligence assistant and you need to engage in a helpful, detailed, polite conversation with a user.",
        },
        {
            "role": "user",
            "content": (
                query
            ),
        },
    ]

    ext_client = OpenAI(api_key=preplexity_ai_key, base_url="https://api.perplexity.ai")

    # chat completion without streaming
    response = ext_client.chat.completions.create(
        model="llama-3.1-sonar-large-128k-online",
        messages=messages,
    )

    response_dict["status_code"] = 200
    response_dict["text"] = response.choices[0].message.content

    return response_dict


PERPLEXITY_CHAT_COMPLETION_FUNCTION_DOCS = """Function: perplexity_api_response

Description:
This function interacts with the Perplexity AI API to generate a concise answer to a user's query by searching the web and synthesizing information from multiple sources.

Use Case:
Use this function as a web search engine to retrieve and compile information into a single, coherent response for queries that require up-to-date or broad information from the internet. 
For best results do not ask too much information in one search, rather break down the query and do multiple searches.

Parameters:
- **query** (string, required): The user's question or search term that needs to be answered using web data.
- **preplexity_ai_key** (string, required): Your API key for authenticating with the Perplexity AI API.

Expected Output:
- **response_content** (string): A compiled answer based on web search results provided by the Perplexity AI.

Example Usage:
```python
# Replace 'YOUR_API_KEY' with your actual Perplexity AI API key
response = perplexity_api_response("What are the latest advancements in AI?", "YOUR_API_KEY")
"""
