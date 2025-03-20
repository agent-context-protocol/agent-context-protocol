from user_data import fetch_search_history, extract_bookmarks, get_calendar_events, get_current_location, get_location_name
from datetime import datetime
import json
import numpy as np
import faiss
import torch
from transformers import AutoTokenizer, AutoModel
from xhtml2pdf import pisa
import latex2mathml.converter as l2m
import re
import io
import os
import subprocess

# def update_interpreter_with_similar_apis(interpreter_message, faiss_index_path='faiss_index.index', model_name='sentence-transformers/all-MiniLM-L6-v2', api_json_path='external_env_details/brief_details.json', k=5):
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
#     with open(api_json_path, 'r') as file:
#         api_data = json.load(file)
    
#     # Prepare the results
#     similar_apis = []
#     api_keys = list(api_data.keys())  # Extract API keys from the data
#     for i, idx in enumerate(indices[0]):
#         if idx < len(api_keys):  # Ensure index is within bounds
#             api_key = api_keys[idx]
#             temp_dict = api_data[api_key]
#             temp_dict['api_name'] = api_key
#             similar_apis.append(temp_dict)

#     # Update the interpreter message dictionary
#     if 'request' not in interpreter_message:
#         interpreter_message['request'] = {}
#     interpreter_message['request']['relevant_apis'] = similar_apis
#     return interpreter_message

def update_interpreter_with_similar_apis(interpreter_message, faiss_index_path='faiss_index.index', model_name='sentence-transformers/all-MiniLM-L6-v2', api_json_path='external_env_details/brief_details.json', k=5):
    # Load the API descriptions
    with open(api_json_path, 'r') as file:
        api_data = json.load(file)
    api_details = []
    for api_name in interpreter_message['request']['relevant_apis']:
        api_details.append({
            'api_name': api_name,
            # 'Input': api_data[api_name]['Input'],
            # 'Output': api_data[api_name]['Output'],
            'Use': api_data[api_name]['Use']
            })
    interpreter_message['request']['relevant_apis'] = api_details
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
    # search_history_list = fetch_search_history("/Users/db/Library/Application Support/Google/Chrome/Default/History")
    search_history_list = []
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
    # bookmarks_list = extract_bookmarks("/Users/db/Library/Application Support/Google/Chrome/Default/Bookmarks")
    bookmarks_list = []
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


def convert_latex_equations_to_mathml(html_content):
    inline_pattern = r'\\\((.*?)\\\)'
    block_pattern = r'\\\[(.*?)\\\]'

    # For block math
    def replace_block(match):
        latex_code = match.group(1).strip()
        mathml = l2m.convert(latex_code)
        return f'<div style="text-align:center;">{mathml}</div>'

    html_content = re.sub(block_pattern, replace_block, html_content, flags=re.DOTALL)

    # For inline math
    def replace_inline(match):
        latex_code = match.group(1).strip()
        mathml = l2m.convert(latex_code)
        return f'<span>{mathml}</span>'

    html_content = re.sub(inline_pattern, replace_inline, html_content, flags=re.DOTALL)

    return html_content

def create_pdf_from_html(html_content, output_filename):
    html_content = convert_latex_equations_to_mathml(html_content)
    with open(output_filename, "wb") as output_file:
        pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=output_file)

    if pisa_status.err:
        print("Error occurred while generating the PDF")
    else:
        print("PDF generated successfully.")


def create_pdf_from_latex(latex_code, output_pdf_path, single_run=False):
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_pdf_path)
    os.makedirs(output_dir, exist_ok=True)

    # Write the LaTeX code to a temporary .tex file in the output directory
    tex_file_name = "temp_latex_file.tex"  # Temporary TeX filename
    tex_file_path = os.path.join(output_dir, tex_file_name)
    with open(tex_file_path, "w") as tex_file:
        tex_file.write(latex_code)

    success_bool = False
    error_messsage = ""
    try:
        # Compile the .tex file into a PDF using latexmk (which handles multiple passes automatically)
        if single_run:
          result = subprocess.run(
              [
                  "pdflatex",             # Generate PDF via pdflatex (could use -xelatex for XeLaTeX, etc.)
                  "-interaction=nonstopmode",    # Do not stop on errors (try to continue compilation)
                  f"-output-directory={output_dir}",  # Directory for output (PDF and aux files)
                  tex_file_path                 # The LaTeX source file to compile
              ],
              check=True,
              capture_output=True,
              text=True
          )
        else:
            result = subprocess.run(
            [
                "latexmk",
                "-pdf",  
                "-f",               # Generate PDF via pdflatex (could use -xelatex for XeLaTeX, etc.)
                "-interaction=nonstopmode",    # Do not stop on errors (try to continue compilation)
                f"-output-directory={output_dir}",  # Directory for output (PDF and aux files)
                tex_file_path                 # The LaTeX source file to compile
            ],
            check=True,
            capture_output=True,
            text=True
        )
        # Print the compilation log from latexmk (stdout and stderr) for debugging
        print("result.stdout: ", result.stdout)
        if result.stderr:
            print("result.stderr : ",result.stderr)

        # Check if the PDF was generated
        generated_pdf = os.path.join(output_dir, tex_file_name.replace(".tex", ".pdf"))
        if os.path.exists(generated_pdf):
            # Rename/move the generated PDF to the desired output path
            os.replace(generated_pdf, output_pdf_path)
            print(f"PDF generated successfully at: {output_pdf_path}")
        else:
            print(f"PDF generation failed. File not found: {generated_pdf}")
        success_bool = True

    except subprocess.CalledProcessError as e:
        # If latexmk exits with an error, print the logs for diagnosis
        print("Error during PDF generation. Please check the LaTeX source and log output.")
        if e.stdout:
            print("e.stdout : ",e.stdout)
            error_messsage += "e.stdout :\n" + e.stdout
        if e.stderr:
            print("e.stderr : ",e.stderr)
            error_messsage += "\ne.stderr :\n" + e.stderr

    finally:
        # Clean up auxiliary files produced during compilation
        aux_extensions = [".aux", ".log", ".out", ".toc", ".fls", ".fdb_latexmk", ".synctex.gz", ".tex"]
        for ext in aux_extensions:
            file_path = os.path.join(output_dir, tex_file_name.replace(".tex", ext))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as remove_err:
                    # If an auxiliary file cannot be removed, print a warning (but continue)
                    print(f"Warning: Could not remove file {file_path}: {remove_err}")
        
    return success_bool, error_messsage

