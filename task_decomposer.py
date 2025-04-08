import json
from base import BaseNode

def update_task_decomposer_with_tools(task_decomposer_message, tool_json_path='external_env_details/brief_details.json'):
    # Load the TOOL descriptions
    with open(tool_json_path, 'r') as file:
        tool_data = json.load(file)
    tool_details = []
    for tool_name in task_decomposer_message['request']['relevant_tools']:
        tool_details.append({
            'tool_name': tool_name,
            'Use': tool_data[tool_name]['Use']
            })
    task_decomposer_message['request']['relevant_tools'] = tool_details
    return task_decomposer_message

class TaskDecompositionNode(BaseNode):
    def __init__(self, node_name, user_query = None, system_prompt = None):
        super().__init__(node_name, system_prompt)
        self.user_query = user_query

    def create_available_tool_string(self):
        # Load the dictionary from the JSON file
        with open('./external_env_details/brief_details.json', 'r') as file:
            tool_details = json.load(file)

        # Start the string with "Available TOOls"
        result_string = "Available TOOls\n\n"

        # Loop through the dictionary and format each TOOl's details
        for tool_name, details in tool_details.items():
            result_string += f"{tool_name}:\n"
            for key, value in details.items():
                result_string += f"  {key}: {value}\n"
            result_string += "\n"

        return result_string


    def setup(self):
        if self.user_query:
            self.chat_history.append({"role": "user", "content": f'''User Query: {self.user_query}'''})
            available_tool_string = self.create_available_tool_string()
            print("available_tool_string : ",available_tool_string)
            self.chat_history.append({"role": "user", "content": available_tool_string})
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
            sub_tasks_list.append(update_task_decomposer_with_tools(sub_task))

        return sub_tasks_list 