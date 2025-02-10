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
import shutil
import tempfile
# from available_apis.browser_tools.main import browser_tools_function
from available_apis.browser_tools_hf.GAIA.main import browser_tools_function

from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor

# Utility function to delete files and directories matching a pattern
def del_stuff_pattern(pattern):
    # Use glob to find all files and directories matching the pattern
    items = glob.glob(pattern, recursive=True)

    for item in items:
        try:
            # Check if it's a file or directory
            if os.path.isfile(item) or os.path.islink(item):
                os.remove(item)  # Remove files or symlinks
                print(f"Deleted file: {item}")
            elif os.path.isdir(item):
                shutil.rmtree(item)  # Remove directories
                print(f"Deleted directory: {item}")
        except Exception as e:
            print(f"Failed to delete {item}. Reason: {e}")

# should run at the start
del_stuff_pattern('./save_viz/*')

def visualization_agent(dict_body):

    response_dict = {}

    if "query" not in dict_body or "response" not in dict_body or "index" not in dict_body:
        response_dict["status_code"] = 400
        response_dict["text"] = "Missing one or more of the required parameters: query, response and index"
        return response_dict
    
    query = dict_body["query"]
    response = dict_body["response"]
    index = int(dict_body["index"])

    # enhancing response with web agent
    web_agent_in_dict = {"query" : f"Query: {query},\n Response: {response}\n Please try to search the web to collect enough information to plot what is asked for in the query while being in accordance with details provided in response, we have to make sure that we have enough datapoints (>2) and in the same units strictly to ensure good plots from the data. You dont have to plot on your own, just collect information please using which we can plot directly. Do not provide a plan for plotting, we need proper numbers we can use for plotting."}
    web_agent_out_dict = browser_tools_function(web_agent_in_dict)
    response = web_agent_out_dict["text"]

    # List of directories to ensure exist
    directories = ['./save_viz/plot', './save_viz/illust']

    for dir_path in directories:
        # Check if the directory exists
        if not os.path.exists(dir_path):
            # Create the directory and any intermediate directories
            os.makedirs(dir_path)
            # print(f"Created directory: {dir_path}")

    llm_client = OpenAI()

    # load the system prompt
    file_path = './available_apis/function_format/visualization_prompt.txt'
    # Read the contents of the file and store it in a variable
    with open(file_path, 'r') as file:
        system_prompt = file.read()
    system_prompt = system_prompt.format(index=index)

    run_success = False
    trial_num = 0
    dalle_prompt = ""
    plots_explanation_string = ""
    code_string = ""
    error_message = ""
    no_plot_bool = False
    
    print("###########")
    while not run_success:
        print("trial_num : ",trial_num)

        # delete some stuff which might be there from previous loop run
        del_stuff_pattern(f'./save_viz/plot/plot_{index}_*')
        del_stuff_pattern(f'./save_viz/illust/illust_{index}*')

        # Prepare the user query
        if code_string == "" and error_message == "" and trial_num == 0:
            user_query = f'''So the user query is : {query},\n and response : {response}.'''
        elif code_string != "" and error_message != "" and trial_num < 5:
            user_query = f'''So the user query is : {query},\n and response : {response}.\n The code we have is {code_string} \n And error that it causes is {error_message}'''
        elif code_string != "" and error_message != "" and trial_num >= 5:
            user_query = f'''So the user query is : {query},\n and response : {response}.\n Plotting is not working out so lets just get the GENERATED_PROMPT'''
        else:
            print(ValueError)
        
        # print("\nuser_query : ",user_query)

        # do the LLM call
        completion = llm_client.chat.completions.create(
            model="gpt-4o",
            messages=[
            {
            "role": "system",
            "content": system_prompt},

            {"role": "user", 
            "content": user_query}
            ]
        )

        plot_respone = completion.choices[0].message.content

        # print("\nplot_respone : ",plot_respone)

        # reset the strings
        dalle_prompt = ""
        plots_explanation_string = ""
        code_string = ""
        error_message = ""

        # print("plot_respone.split: ",plot_respone.split(' '))

        # retrieve the appropriate things from the plot_respone
        if '$$CODE$$' in plot_respone:
            code_string = plot_respone.split("$$CODE$$")[1].split("$$PLOTS_EXPLANATION$$")[0]
            # print("\n code_string : ",code_string)
            
            plots_explanation_string = plot_respone.split("$$CODE$$")[1].split("$$PLOTS_EXPLANATION$$")[1]
            # print("\n plots_explanation_string : ",plots_explanation_string)

            # Create a local command line code executor.
            executor = LocalCommandLineCodeExecutor(
                timeout=20,  # Timeout for each code execution in seconds.
                work_dir='./save_viz/plot',  # Use the temporary directory to store the code files.
            )

            # Create an agent with code executor configuration.
            code_executor_agent = ConversableAgent(
                "code_executor_agent",
                llm_config=False,  # Turn off LLM for this agent.
                code_execution_config={"executor": executor},  # Use the local command line code executor.
                human_input_mode="NEVER",  # Always take human input for this agent for safety.
            )

            try:
                reply = code_executor_agent.generate_reply(messages=[{"role": "user", "content": "```python\n"+code_string+"\n```"}])
    
                run_success = True
                plt.clf()          # Clear the current figure
                plt.close()        # Close the figure window
                plt.rcdefaults()   # Reset matplotlib settings to defaults (optional)
                break
            except Exception as e:
                error_message = str(e)
                print("error_message : ", error_message)
                plt.clf()          # Clear the current figure
                plt.close()        # Close the figure window
                plt.rcdefaults()   # Reset matplotlib settings to defaults (optional)
                trial_num += 1
                continue      

        elif '$$PROMPT$$':
            # dalle_prompt = plot_respone.split("$$PROMPT$$")[1]
            # # print("\ndalle_prompt: ",dalle_prompt)

            # dalle_response, dalle_image_url = visualization_dalle_LLM_Agent(llm_client, plot_respone)
            # img_response = requests.get(dalle_image_url)
            # img_gen = Image.open(BytesIO(img_response.content))

            # # Display the image
            # plt.imshow(img_gen)
            # plt.axis('off')  # Hide axes
            # plt.savefig(f'./save_viz/illust/illust_{index}')
            # plt.clf()          # Clear the current figure
            # plt.close()        # Close the figure window
            # plt.rcdefaults()   # Reset matplotlib settings to defaults (optional)
            # run_success = True
            no_plot_bool = True
            break
        else:
            print("\nErroneous plot_respone : ",plot_respone)
            print(ValueError)

        trial_num += 1

    response_dict["status_code"] = 200

    # if dalle_prompt == "":
    #     # Get the list of matching files with relative paths
    #     files = glob.glob(f'./save_viz/plot/plot_{index}_*')
    #     # Join the list into a single string, separated by newlines
    #     files_string = '\n'.join(files)
    #     response_dict["text"] = plots_explanation_string + f"\nPlots saved at the following paths: {files_string}.\nMore Context and References: {response}." 
    # else:
    #     # Get the list of matching files with relative paths
    #     files = glob.glob(f'./save_viz/illust/illust_{index}*')
    #     # Join the list into a single string, separated by newlines
    #     files_string = '\n'.join(files)
    #     # response_dict["text"] = dalle_prompt + f"\nImages saved at the following paths: {files_string}"
    #     response_dict["text"] = f"\nImages saved at the following paths: {files_string}" 

    if not no_plot_bool:
        # Get the list of matching files with relative paths
        files = glob.glob(f'./save_viz/plot/plot_{index}_*')
        # Join the list into a single string, separated by newlines
        files_string = '\n'.join(files)
        response_dict["text"] = plots_explanation_string + f"\nPlots saved at the following paths: {files_string}.\nMore Context and References: {response}." 
    else:
        response_dict["text"] = f"\nNo Images were saved." 

    return response_dict

def visualization_dalle_LLM_Agent(llm_client, prompt):

    response = llm_client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    size="1024x1024",
    quality="standard",
    n=1,
    )

    image_url = response.data[0].url

    return response, image_url

VISUALIZATION_AGENT_FUNCTION_DOCS = """Function: visualization_agent

Description:
This function generates visualizations (plots or images) based on a user's query and the system's response. It can create plots by executing generated code.

Use Case:
Use this function to create visual representations that complement textual information, enhancing understanding or providing illustrative support for data and concepts. It's ideal for generating charts, graphs. Strictly every panel should have only one visualization agent step.

Parameters:
- query (string, required): The user's initial question or request that requires visualization.
- response (string, required): The system's textual response to the query, providing context for generating the visualization.
- index (string, required): An identifier used to save and reference the generated visualization files uniquely. We have to pass the current panel number.

Expected Output:
- response_content (string): An explanation of the generated plots or in the case when no plot was genrated it will output: No Images were saved.

Example Usage:
```python
dict_body = {
    "query": "Please plot the GDP growth of the top 5 economies over the last decade.",
    "response": "The GDP growth of the top 5 economies varies over the last decade, with some fluctuations.",
    "index": 1
}

response = visualization_agent(dict_body)
print(response["text"])"""

# VISUALIZATION_AGENT_FUNCTION_DOCS = """Function: visualization_agent

# Description:
# This function generates visualizations (plots or images) based on a user's query and the system's response. It can create plots by executing generated code or produce images using text prompts for image generation models like DALL·E.

# Use Case:
# Use this function to create visual representations that complement textual information, enhancing understanding or providing illustrative support for data and concepts. It's ideal for generating charts, graphs, or illustrative images corresponding to the provided query and response. Strictly every panel should have only one visualization agent step.

# Parameters:
# - query (string, required): The user's initial question or request that requires visualization.
# - response (string, required): The system's textual response to the query, providing context for generating the visualization.
# - index (string, required): An identifier used to save and reference the generated visualization files uniquely. We have to pass the current panel number.

# Expected Output:
# - response_content (string): An explanation of the generated plots or the image prompt used for image generation.

# Example Usage:
# ```python
# dict_body = {
#     "query": "Please plot the GDP growth of the top 5 economies over the last decade.",
#     "response": "The GDP growth of the top 5 economies varies over the last decade, with some fluctuations.",
#     "index": 1
# }

# response = visualization_agent(dict_body)
# print(response["text"])"""

# dict_body_ex = {
#     "query": "Please plot the GDP of the 5 largest economies in the world.",
#     "response": "The GDP of the top 5 economies in the world.",
#     "index": 1
# }
# ex_out = visualization_agent(dict_body_ex)
# print("ex_out : ",ex_out)