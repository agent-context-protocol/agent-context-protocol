import asyncio
from orchestrator import MainOrchestrator
from available_apis.browser_tools.mdconvert import MarkdownConverter, UnsupportedFormatException, FileConversionException
import re
import json
from openai import OpenAI
import base64

client = OpenAI()

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
    
def vision_qa(query, user_image_path):
        base64_image = encode_image(user_image_path)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Please provide an description of the image according to the query, though do not strictly answer the query and just provide a description which can help answer the query.\n Query: {query}"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )

        return response.choices[0].message.content


def extract_file_path(query):
    match = re.search(r'Attachment: file://(\S+)', query)
    if match:
        return match.group(1)
    else:
        return None

def reformat_query_with_attachment_content(user_query):

    mdconvert_obj = MarkdownConverter()

    # Check if there's an attachment and extract the file path
    file_path = extract_file_path(user_query)

    if ".jpg" in file_path or ".jpeg" in file_path or ".png" in file_path:
        text_content = vision_qa(user_query, file_path)
        print(f"text_content : {text_content}")
    else:
        # Convert the file content
        res = mdconvert_obj.convert_local(file_path)
        text_content = res.text_content
    
    # Reformat the query with the question and attachment content
    # reformatted_query = f"question: {user_query.split('Attachment: file://')[0].strip()}\n"
    reformatted_query = f"question: {user_query}\n"
    reformatted_query += f"Attachment File Content:\n{text_content}"
    
    # # Display extracted details for confirmation
    # print("Result title:", res.title)
    # print("Result text content:", res.text_content)
    
    return reformatted_query

async def run_orch_func(user_query):
    orchestrator = MainOrchestrator()

    # if user query has a file attachement
    if "Attachment: file://" in user_query:
        user_query = reformat_query_with_attachment_content(user_query)
        print("user_query : ",user_query)
        # print(cause_Error)
        

    # Initialize the workflow
    workflow = await orchestrator.initialise(user_query)

    outputs={}
    async for group_id, group_results in orchestrator.run(user_query, workflow):
        outputs[group_id] = group_results

    print("Workflow completed!")

    # Load the string back
    with open('GAIA_Answer.json', 'r') as file:
        gaia_answer = json.load(file)

    return gaia_answer
