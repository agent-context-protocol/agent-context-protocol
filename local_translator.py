from base import BaseNode
from available_apis.hardcoded_format.return_dict import HARDCODED_APIS_DICT
from available_apis.openapi_format.return_dict import OPEN_APIS_DICT
import json

class LocalTranslatorNode(BaseNode):
    def __init__(self, node_id, panel_description, system_prompt=None):
        super().__init__(node_id, system_prompt)
        self.panel_description = panel_description
        self.workflow = None

        self.get_system_prompts()
        self.get_api_keys()

    def get_system_prompts(self):
        # workflow_creation_prompt
        with open('prompts/local_translator/workflow_finalization_prompt.txt', 'r') as file:
            self.workflow_finalization_prompt = file.read()

    def get_api_keys(self):
        with open("./external_env_details/api_keys.json", "r") as json_file:
            self.api_keys = json.load(json_file)

    # input format prep functions
    def prepare_input_for_api_running_step(self, step, api_documentation):
        """
        Prepare the input for a single step in the workflow.
        
        Args:
            step (dict): The workflow step that contains the API details, input vars, output vars, etc.
            api_description (dict): The API description (loaded from a dictionary based on API name).
            
        Returns:
            dict: The prepared input data for the API request.
        """
        input_string = "\nPlease generate output for this input:\n"
        input_string += "Step Details:\n"

        input_string += f"- API: {step['api']}\n"
        input_string += f"- Handles: {step['handles']}\n"
        
        # Input variables section
        input_string += "- Input Variables:\n"
        for var in step['input_vars']:
            input_string += f"  - Name: {var['name']}\n"
            input_string += f"    - Parameter: {var['parameter']}\n"
            input_string += f"    - Type: {var['type']}\n"
            input_string += f"    - Source: {var['source']}\n"
            input_string += f"    - Description: {var['description']}\n"
            input_string += f"    - Value: \"{var['value']}\"\n"

        # Output variables section
        input_string += "- Output Variables:\n"
        for var in step['output_vars']:
            input_string += f"  - Name: {var['name']}\n"
            input_string += f"    - Description: {var['description']}\n"

        # # Add dependencies if any
        # if step.get("dependencies"):
        #     input_string += "- Dependencies:\n"
        #     dependencies_str = ', '.join([f"Panel {d['panel']}, Step {d['step']}" for d in step['dependencies']])
        #     input_string += f"  - {dependencies_str}\n"
        # else:
        #     input_string += "- Dependencies: None\n"

        # Add the input details
        if step['api'] in self.api_keys:
            input_string += "\nAdditonal Input Details:\n"
            input_string += f"API_KEY: {self.api_keys[step['api']]}\n"

        # Add the API documentation provided
        input_string += "\nAPI Documentation:\n"
        input_string += api_documentation

        return input_string


    def build_verify(self):
        """
        This function goes through each step of the workflow and prepares inputs based on the workflow details
        and the API descriptions provided.
        
        Args:
            api_descriptions (dict): Dictionary where the key is the API name and the value is the API description.
        """
        if not self.workflow:
            raise ValueError("No workflow found for this panel.")
        
        num_steps = len(self.workflow)
        
        # preperation of input data for detailed workflow creation
        input_data_list = []
        for s_i in range(num_steps):
            step = self.workflow[str(s_i+1)]
            print(f"Processing Step {s_i+1} for API: {step['api']}")
            # Call the function to prepare the input for the current step
            if step['api'] in OPEN_APIS_DICT:
                api_documentation = OPEN_APIS_DICT[step['api']]
            elif step['api'] in HARDCODED_APIS_DICT:
                api_documentation = HARDCODED_APIS_DICT[step['api']]
            else:
                raise ValueError("API Documentation Not Found.")
            input_data = self.prepare_input_for_api_running_step(step, api_documentation)
            input_data_list.append(input_data)
            # print(f"Prepared input for step {step['step']}: {input_data}")

        print("input_data_list[0] : ",input_data_list[0])

        # generating the workflow from the LLM
        self.chat_history.append({"role": "system", "content": self.workflow_finalization_prompt}) # system prompt for workflow_creation
        self.chat_history.append({"role": "user", "content": input_data_list[0]})

        llm_response_workflow = self.generate()
        print("llm_response_workflow : ",llm_response_workflow)
            
