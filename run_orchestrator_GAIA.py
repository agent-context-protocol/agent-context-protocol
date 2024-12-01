import asyncio
from orchestrator import MainOrchestrator
from available_apis.browser_tools.mdconvert import MarkdownConverter, UnsupportedFormatException, FileConversionException
import re
import json


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
    
    # Convert the file content
    res = mdconvert_obj.convert_local(file_path)
    
    # Reformat the query with the question and attachment content
    reformatted_query = f"question: {user_query.split('Attachment: file://')[0].strip()}\n"
    reformatted_query += f"Attachment File Content:\n{res.text_content}"
    
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