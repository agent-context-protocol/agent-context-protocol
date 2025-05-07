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

def visualization_dalle_LLM_Agent(prompt, open_ai_key):

    llm_client = llm_client = OpenAI(api_key=open_ai_key)

    response = llm_client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    size="1024x1024",
    quality="standard",
    n=1,
    )

    image_url = response.data[0].url

    return response, image_url