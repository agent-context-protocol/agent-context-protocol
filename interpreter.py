from utils import fetch_user_data, update_interpreter_with_similar_apis
import json
from base import BaseNode
from available_apis.browser_tools.main import browser_tools_function

class InterpreterNode(BaseNode):
    def __init__(self, node_name, user_query = None, system_prompt = None, personal_json = 'personal_info.json'):
        super().__init__(node_name, system_prompt)
        self.user_query = user_query
        with open(personal_json, 'r') as file:
            data = json.load(file)
        self.personal_json = data

    def create_available_api_string(self):
        # Load the dictionary from the JSON file
        with open('./external_env_details/brief_details.json', 'r') as file:
            api_details = json.load(file)

        # Start the string with "Available APIs"
        result_string = "Available APIs\n\n"

        # Loop through the dictionary and format each API's details
        for api_name, details in api_details.items():
            result_string += f"{api_name}:\n"
            for key, value in details.items():
                result_string += f"  {key}: {value}\n"
            result_string += "\n"

        return result_string


    def setup(self):
        if self.user_query:
            # initial_message = fetch_user_data(self.personal_json, self.user_query)
            # print('User Context: ',initial_message)
            suggested_sections = browser_tools_function({"query": f"Please provide what sections/subsections should be kept for a detailed and comprehensive report being written on the topic: {self.user_query}"}, True)
            print(f"\nUser Query: {self.user_query} \n\n Suggested Sections and Sub-Sections for the report:\n{suggested_sections['text']}")
            self.chat_history.append({"role": "user", "content": f'''User Query: {self.user_query} \n\n Suggested Sections and Sub-Sections for the report:\n{suggested_sections['text']}'''})
            available_api_string = self.create_available_api_string()
            print("available_api_string : ",available_api_string)
            self.chat_history.append({"role": "user", "content": available_api_string})
            output = self.generate()
            print(output)
            output = self.modify_message(output)
            return output

    def modify_message(self, message):
        # Define the JSON-like strings
        json_strings = message.split('---Done---')[1:-1]
        panels_list = []
        for json_string in json_strings:
            panel = json.loads(json_string)
            instance_id = panel["instance_id"]
            panels_list.append(update_interpreter_with_similar_apis(panel))

        return panels_list 
    
'''
Still Need to implement how the communication between interpreter and the translator will be handled after the initial setup.
'''