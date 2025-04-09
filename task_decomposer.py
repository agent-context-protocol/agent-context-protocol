from utils import fetch_user_data, update_task_decomposer_with_similar_tools
import json
from base import BaseNode
# from available_tools.browser_tools.main import browser_tools_function
from available_tools.browser_tools_hf.GAIA.main import browser_tools_function
import datetime

class TaskDecompositionNode(BaseNode):
    def __init__(self, node_name, user_query = None, system_prompt = None):
        super().__init__(node_name, system_prompt)
        self.user_query = user_query

    def create_available_tool_string(self):
        # Load the dictionary from the JSON file
        with open('./external_env_details/brief_details.json', 'r') as file:
            tool_details = json.load(file)

        # Start the string with "Available Tools"
        result_string = "Available Tools\n\n"

        # Loop through the dictionary and format each TOOl's details
        for tool_name, details in tool_details.items():
            result_string += f"{tool_name}:\n"
            for key, value in details.items():
                result_string += f"  {key}: {value}\n"
            result_string += "\n"

        return result_string

    def setup(self):
        now = datetime.datetime.utcnow().isoformat()
        event = {
            "timestamp": now + "Z",  # E.g. "2025-03-24T14:55:00.123456Z"
            "description": "ProtocolInitiationStarted"
        }
        BaseNode.events.append(event)
        if self.user_query:
            # run_success = False
            run_count=0
            while run_count<5:
                # try:
                run_count += 1
                suggested_sections = browser_tools_function({"query": f"Please provide what sections/subsections should be kept for a detailed and comprehensive report being written on the topic. You need to search the web on the topic (as if you were writing the report) to figure out the best sections to focus on based on the current trends and knowledge about the topic in the world.): {self.user_query}"}, True)
                print(f"\nUser Query: {self.user_query} \n\n Suggested Sections and Sub-Sections for the report:\n{suggested_sections['text']}")
                self.chat_history.append({"role": "user", "content": f'''User Query: {self.user_query} \n\n Suggested Sections and Sub-Sections for the report:\n{suggested_sections['text']}'''})
                available_tool_string = self.create_available_tool_string()
                print("available_tool_string : ",available_tool_string)
                self.chat_history.append({"role": "user", "content": available_tool_string})
                output = self.generate()
                print(output)
                # with open("interpreter_task_decomp.txt", "w") as f:
                #     f.write(output)
                output = self.modify_message(output)
                return output
                # except Exception as e:
                #     print("Error: ",str(e))
                #     continue

    def modify_message(self, message):
        # Define the JSON-like strings
        json_strings = message.split('---Done---')[1:-1]

        # for json_string in json_strings:
        #     print("json_string : ",json_string)
        #     print("\n\n")
        # if json_strings[0] != '':
        #     json_strings = json_strings[:-1]
        # else:
        #     json_strings = json_strings[1:-1]
        
        sub_tasks_list = []
        for json_string in json_strings:
            sub_task = json.loads(json_string)
            instance_id = sub_task["instance_id"]
            sub_tasks_list.append(update_task_decomposer_with_similar_tools(sub_task))

        return sub_tasks_list 
    
'''
Still Need to implement how the communication between interpreter and the translator will be handled after the initial setup.
'''