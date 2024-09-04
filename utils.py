from user_data import fetch_search_history, extract_bookmarks, get_calendar_events, get_current_location, get_location_name
from datetime import datetime
import json
import numpy as np
import faiss
import torch
from transformers import AutoTokenizer, AutoModel

def update_interpreter_with_similar_apis(interpreter_message, faiss_index_path='faiss_index.index', model_name='sentence-transformers/all-MiniLM-L6-v2', api_json_path='api_json_file.json', k=5):
    # Load the FAISS index
    index = faiss.read_index(faiss_index_path)

    # Load pre-trained model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    # Generate embedding for the interpreter description
    interpreter_description = interpreter_message['panel_description']
    inputs = tokenizer([interpreter_description], return_tensors='pt', padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    interpreter_embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()

    # Perform similarity search
    distances, indices = index.search(interpreter_embedding, k)

    # Load the API descriptions
    with open(api_json_path, 'r') as file:
        api_data = json.load(file)
    
    # Prepare the results
    similar_apis = []
    api_keys = list(api_data.keys())  # Extract API keys from the data
    for i, idx in enumerate(indices[0]):
        if idx < len(api_keys):  # Ensure index is within bounds
            api_key = api_keys[idx]
            similar_apis.append({
                api_key: api_data[api_key]  # Include all details for the API
            })

    # Update the interpreter message dictionary
    if 'request' not in interpreter_message:
        interpreter_message['request'] = {}
    interpreter_message['request']['relevant_apis'] = similar_apis
    return interpreter_message

def convert_calendar_event(input_str):
    # Split the input string to separate the date-time part and the event description
    datetime_str, event_description = input_str.split(' ', 1)
    
    # Parse the datetime string to a datetime object
    datetime_obj = datetime.fromisoformat(datetime_str)
    
    # Format the datetime object to the desired format
    formatted_date = datetime_obj.strftime("%B %d, %Y")
    
    # Construct the final output string
    result = f"{event_description} on {formatted_date}"
    
    return result 

def fetch_user_data(personal_info, original_query):
    # Fetch search history
    prompt = f'''
1. Personal Information:
* Age: {personal_info['age']}
* Language: {personal_info['language']}
* Location: {personal_info['location']}
* Professional Background: {personal_info['professional_background']}
    '''
    search_history_list = fetch_search_history("/Users/db/Library/Application Support/Google/Chrome/Default/History")
    search_history = '\n2. Search History:\n'
    for entry in search_history_list:
        search_history += f'''* {entry}\n'''
    
    prompt += search_history

    # Get current location
    current_location = get_current_location()
    if current_location:
        location_name = get_location_name(current_location['latitude'], current_location['longitude'], current_location['city'])
        if location_name:
            prompt += f'''\n3. Current Location:\n* {location_name}\n'''

    # Extract bookmarks
    bookmarks_list = extract_bookmarks("/Users/db/Library/Application Support/Google/Chrome/Default/Bookmarks")
    bookmarks = '\n4. Bookmarks:\n'
    for bookmark in bookmarks_list[:5]:
        bookmarks += f'''* {bookmark['name']}\n'''
    prompt += bookmarks

    # Retrieve calendar events
    # 'credentials.json', 'token.json' these files are generated after setting up a google cloud project and enabling google calendar api
    calendar_events_list = get_calendar_events('credentials.json', 'token.json')
    calendar_events = '\n5. Calendar Events:\n'
    for event in calendar_events_list[:5]:
        calendar_events += f'''* {convert_calendar_event(event['start'] +' '+ event['summary'])}\n'''
    prompt += calendar_events

    prompt += f'''\nOriginal Query: {original_query}\n'''
    return prompt