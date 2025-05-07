import json
from importlib import resources
import agent_context_protocol.external_env_details as env_details
from .base import BaseNode

class TaskDecompositionNode(BaseNode):
    def __init__(self, node_name, user_query = None, system_prompt = None, mcp_tool_manager = None):
        super().__init__(node_name, system_prompt)
        self.user_query = user_query
        self.mcp_tool_manager = mcp_tool_manager

    def create_available_tool_string(self):
        with resources.open_text(env_details, "brief_details.json") as file:
            tool_details = json.load(file)

        # Start the string with "Available TOOls"
        result_string = "Available TOOls\n\n"

        # Loop through the dictionary and format each TOOl's details
        for tool_name, details in tool_details.items():
            result_string += f"{tool_name}:\n"
            for key, value in details.items():
                result_string += f"  {key}: {value}\n"
            result_string += "\n"

        if self.mcp_tool_manager:
            result_string += "MCP Tools:\n\n"
            mcp_tool_names = self.mcp_tool_manager.list_all_tools()
            for tool_name, description in mcp_tool_names.items():
                result_string += f" {tool_name}: {description}\n\n"

        return result_string


    def setup(self):
        try_count = 0
        while try_count < 5:
            try_count += 1
            try:
                if self.user_query:
                    self.chat_history.append({"role": "user", "content": f'''User Query: {self.user_query}'''})
                    available_tool_string = self.create_available_tool_string()
                    print("available_tool_string : ",available_tool_string)
                    self.chat_history.append({"role": "user", "content": available_tool_string})
                    output = self.generate()
                    print(output)
                    output = self.modify_message(output)
                    return output
            except Exception as e:
                print(f"Error in Task Decompose, Trying Again. Error Details: {str(e)}")
        
        raise ValueError("Task Decomposer Failed")

    def update_task_decomposer_with_tools(self, task_decomposer_message):
        # Load the TOOL descriptions
        with resources.open_text(env_details, "brief_details.json") as file:
            tool_data = json.load(file)
        tool_details = []
        if self.mcp_tool_manager:
            mcp_tool_names = self.mcp_tool_manager.list_all_tools()
            for tool_name, description in mcp_tool_names.items():
                tool_data[tool_name] = {
                    "Use": description
                }

        # print(tool_data)
        for tool_name in task_decomposer_message['request']['relevant_tools']:
            tool_details.append({
                'tool_name': tool_name,
                'Use': tool_data[tool_name]['Use']
                })
        task_decomposer_message['request']['relevant_tools'] = tool_details
        return task_decomposer_message

    def modify_message(self, message):
        # Define the JSON-like strings
        json_strings = message.split('---Done---')[1:-1]
        sub_tasks_list = []
        for json_string in json_strings:
            sub_task = json.loads(json_string)
            instance_id = sub_task["instance_id"]
            sub_tasks_list.append(self.update_task_decomposer_with_tools(sub_task))

        return sub_tasks_list 
    