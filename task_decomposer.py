import json
from base import BaseNode

def update_task_decomposer_with_apis(task_decomposer_message, api_json_path='external_env_details/brief_details.json'):
    # Load the API descriptions
    with open(api_json_path, 'r') as file:
        api_data = json.load(file)
    api_details = []
    for api_name in task_decomposer_message['request']['relevant_apis']:
        api_details.append({
            'api_name': api_name,
            'Use': api_data[api_name]['Use']
            })
    task_decomposer_message['request']['relevant_apis'] = api_details
    return task_decomposer_message

class TaskDecompositionNode(BaseNode):
    def __init__(self, node_name, user_query = None, system_prompt = None):
        super().__init__(node_name, system_prompt)
        self.user_query = user_query

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
            self.chat_history.append({"role": "user", "content": f'''User Query: {self.user_query}'''})
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
        sub_tasks_list = []
        for json_string in json_strings:
            sub_task = json.loads(json_string)
            instance_id = sub_task["instance_id"]
            sub_tasks_list.append(update_task_decomposer_with_apis(sub_task))

        return sub_tasks_list 