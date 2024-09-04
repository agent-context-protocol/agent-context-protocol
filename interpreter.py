from utils import fetch_user_data, update_interpreter_with_similar_apis
import json
from base import BaseNode

class InterpreterNode(BaseNode):
    def __init__(self, node_name, user_query = None, system_prompt = None, personal_json = None):
        super().__init__(node_name, system_prompt)
        self.user_query = user_query
        self.personal_json = personal_json

    def setup(self):
        if self.user_query:
            initial_message = fetch_user_data(self.personal_json, self.user_query)
            self.chat_history.append({"role": "user", "content": initial_message})
            self.modify_message(self.generate())

    def modify_message(self, message):
        # Define the JSON-like strings
        json_strings = message
        panels_dict = {}
        for json_string in json_strings:
            panel = json.loads(json_string)
            instance_id = panel["instance_id"]
            panels_dict[instance_id] = update_interpreter_with_similar_apis(panel)

        return panels_dict
    
'''
Still Need to implement how the communication between interpreter and the translator will be handled after the initial setup.
'''