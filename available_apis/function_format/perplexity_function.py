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
def perplexity_api_response(query):

    preplexity_ai_key = "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"

    # # load the system prompt
    # file_path = '/Users/aarjun1/Documents/Arjun/Princeton_Work/myCode/external_env_prompts/preplexity.txt'
    # # Read the contents of the file and store it in a variable
    # with open(file_path, 'r') as file:
    #     system_prompt = file.read()

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

    return response.choices[0].message.content