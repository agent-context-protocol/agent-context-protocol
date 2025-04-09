from user_data import fetch_search_history, extract_bookmarks, get_calendar_events, get_current_location, get_location_name
from datetime import datetime
import json
import numpy as np
import faiss
import torch
from transformers import AutoTokenizer, AutoModel

# def update_interpreter_with_similar_tools(interpreter_message, faiss_index_path='faiss_index.index', model_name='sentence-transformers/all-MiniLM-L6-v2', tool_json_path='external_env_details/brief_details.json', k=5):
#     # Load the FAISS index
#     index = faiss.read_index(faiss_index_path)

#     # Load pre-trained model and tokenizer
#     tokenizer = AutoTokenizer.from_pretrained(model_name)
#     model = AutoModel.from_pretrained(model_name)

#     # Generate embedding for the interpreter description
#     interpreter_description = interpreter_message['panel_description']
#     inputs = tokenizer([interpreter_description], return_tensors='pt', padding=True, truncation=True)
#     with torch.no_grad():
#         outputs = model(**inputs)
#     interpreter_embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()

#     # Perform similarity search
#     distances, indices = index.search(interpreter_embedding, k)

#     # Load the API descriptions
#     with open(tool_json_path, 'r') as file:
#         tool_data = json.load(file)
    
#     # Prepare the results
#     similar_apis = []
#     api_keys = list(tool_data.keys())  # Extract API keys from the data
#     for i, idx in enumerate(indices[0]):
#         if idx < len(api_keys):  # Ensure index is within bounds
#             api_key = api_keys[idx]
#             temp_dict = tool_data[api_key]
#             temp_dict['tool_name'] = api_key
#             similar_apis.append(temp_dict)

#     # Update the interpreter message dictionary
#     if 'request' not in interpreter_message:
#         interpreter_message['request'] = {}
#     interpreter_message['request']['relevant_tools'] = similar_apis
#     return interpreter_message

def update_task_decomposer_with_similar_tools(interpreter_message, faiss_index_path='faiss_index.index', model_name='sentence-transformers/all-MiniLM-L6-v2', tool_json_path='external_env_details/brief_details.json', k=5):
    # Load the TOOL descriptions
    with open(tool_json_path, 'r') as file:
        tool_data = json.load(file)
    tool_details = []
    for tool_name in interpreter_message['request']['relevant_tools']:
        tool_details.append({
            'tool_name': tool_name,
            # 'Input': tool_data[tool_name]['Input'],
            # 'Output': tool_data[tool_name]['Output'],
            'Use': tool_data[tool_name]['Use']
            })
    interpreter_message['request']['relevant_tools'] = tool_details
    return interpreter_message