from base import BaseNode
from available_apis.hardcoded_format.return_dict import HARDCODED_APIS_DICT
from available_apis.openapi_format.return_dict import OPEN_APIS_DICT
from available_apis.function_format.return_dict import FUNCTION_APIS_DOCUMENTATION_DICT, FUNCTION_APIS_FUNCTION_DICT
from available_apis.rapid_apis_format.return_dict import RAPID_APIS_DICT
import json
import requests
import re
import asyncio
import time
import tiktoken

class LocalTranslatorNode(BaseNode):
    def __init__(self, panel_no, panel_description, system_prompt=None, main_translator=None):
        super().__init__(panel_no, system_prompt)
        self.panel_no = panel_no
        self.panel_description = panel_description
        self.group_workflow = None
        self.panel_workflow = None
        self.main_translator = main_translator
        self.group_id = None

        self.prev_status_update = None

        self.get_system_prompts()
        self.get_api_keys()

        self.drop = False
        self.modify = False

    def get_system_prompts(self):
        # api_running_prompt
        with open('prompts/local_translator/api_running_prompt.txt', 'r') as file:
            self.api_running_prompt = file.read()
        
        # api_output_prompt
        with open('prompts/local_translator/api_output_prompt.txt', 'r') as file:
            self.api_output_prompt = file.read()

        # status/assistance prompt
        with open('prompts/local_translator/status_assistance_prompt.txt', 'r') as file:
            self.status_assistance_prompt = file.read()

        # user_readable_output_prompt
        with open('prompts/local_translator/user_readable_output_prompt.txt', 'r') as file:
            self.user_readable_output_prompt = file.read()

        # api summarize prompt
        with open('prompts/local_translator/api_output_summarizer_prompt.txt', 'r') as file:
            self.api_output_summarizer_prompt = file.read()

    def get_api_keys(self):
        with open("./external_env_details/api_keys.json", "r") as json_file:
            self.api_keys = json.load(json_file)

    ###################################################################
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
        # in case its a rapid api
        elif step['api'] in RAPID_APIS_DICT:
            input_string += "\nAdditonal Input Details:\n"
            rapid_api_key = self.api_keys["Rapid_API_Key"]
            input_string += f"API_KEY: {rapid_api_key}\n"

        # Add the API documentation provided
        input_string += "\nAPI Documentation:\n"
        input_string += api_documentation

        return input_string
    
    def prepare_input_for_api_output(self, api_response, panel_no, step_no):
        result_str = ""

        # Get the current panel and step data
        panel_data = self.group_workflow[str(panel_no)]
        step_data = panel_data['steps'][str(step_no)]

        # Extract step details for the current step
        api_name = step_data['api']
        handles = step_data['handles']

        # Begin constructing the input string for the current step
        result_str += f"Current Step Details:\n\n- API: {api_name}\n- Handles: {handles}\n"

        # Add Input Variables for the current step
        result_str += "- Input Variables:\n"
        for input_var in step_data['input_vars']:
            result_str += f"  - Name: {input_var['name']}\n"
            result_str += f"    - Parameter: {input_var['parameter']}\n"
            result_str += f"    - Type: {input_var['type']}\n"
            result_str += f"    - Source: {input_var['source']}\n"
            result_str += f"    - Description: {input_var['description']}\n"
            result_str += f"    - Value: \"{input_var['value']}\"\n"

        # Add Output Variables for the current step
        result_str += "- Output Variables:\n"
        for output_var in step_data['output_vars']:
            result_str += f"  - Name: {output_var['name']}\n"
            result_str += f"    - Description: {output_var['description']}\n"

        # Check if any output is used by dependent steps
        has_dependent_steps = False
        visited_panel_steps = []
        for output_var in step_data['output_vars']:
            if output_var['used_by']:
                if not has_dependent_steps:
                    # Add the dependent section header only once
                    result_str += f"\nDependent Input Variables Step Details:\n"
                    has_dependent_steps = True

                for dependent in output_var['used_by']:
                    dependent_panel_no = dependent['panel']
                    dependent_step_no = dependent['step']
                    if [dependent_panel_no, dependent_step_no] in visited_panel_steps:
                        continue
                    visited_panel_steps.append([dependent_panel_no, dependent_step_no])
                    
                    # Fetch the dependent step data from the appropriate panel
                    dependent_panel_data = self.group_workflow[str(dependent_panel_no)]
                    dependent_step_data = dependent_panel_data['steps'][str(dependent_step_no)]

                    result_str += f"\nPanel {dependent_panel_no}, Step {dependent_step_no}:\n"
                    result_str += f"- API: {dependent_step_data['api']}\n"
                    result_str += f"- Handles: {dependent_step_data['handles']}\n"
                    result_str += "- Input Variables:\n"

                    for dep_input_var in dependent_step_data['input_vars']:
                        result_str += f"  - Name: {dep_input_var['name']}\n"
                        result_str += f"    - Parameter: {dep_input_var['parameter']}\n"
                        result_str += f"    - Type: {dep_input_var['type']}\n"
                        result_str += f"    - Source: {dep_input_var['source']}\n"
                        result_str += f"    - Description: {dep_input_var['description']}\n"
                        result_str += f"    - Value: {dep_input_var['value']}\n"

        # Append the API Response at the end
        for api_ind, api_resp in enumerate(api_response):
            result_str += f"\nAPI Response {api_ind}:\n\n{api_resp}\n"
        
        return result_str
    
    def prepare_input_for_api_output_summarize(self, api_response, panel_no, step_no):
        result_str = f"{self.api_output_summarizer_prompt}"

        # Get the current panel and step data
        panel_data = self.group_workflow[str(panel_no)]
        step_data = panel_data['steps'][str(step_no)]

        # Check if any output is used by dependent steps
        has_dependent_steps = False
        visited_panel_steps = []
        for output_var in step_data['output_vars']:
            if output_var['used_by']:
                if not has_dependent_steps:
                    # Add the dependent section header only once
                    result_str += f"\nDependent Input Variables Step Details:\n"
                    has_dependent_steps = True

                for dependent in output_var['used_by']:
                    dependent_panel_no = dependent['panel']
                    dependent_step_no = dependent['step']
                    if [dependent_panel_no, dependent_step_no] in visited_panel_steps:
                        continue
                    visited_panel_steps.append([dependent_panel_no, dependent_step_no])
                    
                    # Fetch the dependent step data from the appropriate panel
                    dependent_panel_data = self.group_workflow[str(dependent_panel_no)]
                    dependent_step_data = dependent_panel_data['steps'][str(dependent_step_no)]

                    result_str += f"\nPanel {dependent_panel_no}, Step {dependent_step_no}:\n"
                    result_str += f"- API: {dependent_step_data['api']}\n"
                    result_str += f"- Handles: {dependent_step_data['handles']}\n"
                    result_str += "- Input Variables:\n"

                    for dep_input_var in dependent_step_data['input_vars']:
                        result_str += f"  - Name: {dep_input_var['name']}\n"
                        result_str += f"    - Parameter: {dep_input_var['parameter']}\n"
                        result_str += f"    - Type: {dep_input_var['type']}\n"
                        result_str += f"    - Source: {dep_input_var['source']}\n"
                        result_str += f"    - Description: {dep_input_var['description']}\n"
                        result_str += f"    - Value: {dep_input_var['value']}\n"

        # Append the API Response at the end
        result_str += f"\nAPI Response :\n\n{api_response}\n"
        
        return result_str
    
    # def prepare_status_assistance_input(self, workflow_dict, step_no, error_dict = None):
    #     # Initialize the formatted result string
    #     result = []
        
    #     # Extract panel description
    #     panel_data = workflow_dict[str(self.panel_no)]
    #     panel_description = panel_data["panel_description"]
        
    #     # Workflow details
    #     result.append("Workflow:")
    #     result.append(f"Panel Description: {panel_description}")
    #     result.append("\nWorkflow Steps:")
        
    #     # Iterate through each step and build the formatted input
    #     steps = panel_data["steps"]
    #     for step_key, step_data in steps.items():
    #         # if int(step_key) > step_no:
    #         #     break
            
    #         # Add step details
    #         result.append(f"\nStep {step_key}")
    #         result.append(f"- API: {step_data['api']}")
    #         result.append(f"- Handles: {step_data['handles']}")
            
    #         # Input Variables
    #         result.append("- Input Variables:")
    #         for input_var in step_data['input_vars']:
    #             result.append(f"  - Name: {input_var['name']}")
    #             result.append(f"    - Parameter: {input_var['parameter']}")
    #             result.append(f"    - Type: {input_var['type']}")
    #             result.append(f"    - Source: {input_var['source']}")
    #             result.append(f"    - Description: {input_var['description']}")
    #             result.append(f"    - Value: {input_var.get('value', 'None')}")
            
    #         # Output Variables
    #         result.append("- Output Variables:")
    #         for output_var in step_data['output_vars']:
    #             result.append(f"  - Name: {output_var['name']}")
    #             result.append(f"    - Description: {output_var['description']}")
        
    #     # Add Current API Step
    #     result.append(f"\nCurrent API Step: Panel {self.panel_no}, Step {step_no}")
        
    #     # Add Previous Status Update (if exists)
    #     previous_update_str = "\nPrevious Status Update:\n"
        
    #     if self.prev_status_update:
    #         prev_status = self.prev_status_update
    #         previous_update_str += "\n- Progress:"
    #         previous_update_str += f"\n  - Previous Progress:\n    - {prev_status['previous_progress']}"
    #         previous_update_str += f"\n  - Current Progress:\n    - {prev_status['current_progress']}"
    #         previous_update_str += f"\n- Current Step: Panel {prev_status['current_step']['panel']}, Step {prev_status['current_step']['step']}"
    #         previous_update_str += "\n- Completed APIs:"
    #         for api in prev_status['completed_apis']:
    #             previous_update_str += f"\n  - {api['name']}:"
    #             previous_update_str += f"\n    - Purpose: {api['purpose']}"
    #             previous_update_str += f"\n    - Accomplished: {api['accomplished']}"
    #         previous_update_str += f"\n- Encountered Issues: {prev_status['issues']}"
        
    #     result.append(previous_update_str)

    #     # Add Assistance Request Needed section if error_dict is provided
    #     if error_dict:
    #         assistance_request_str = "\nAssistance Request Needed, Error is:\n"
    #         assistance_request_str += f"{str(error_dict)}"  # Convert the entire error_dict to string and add it
    #         result.append(assistance_request_str)

    #     # Join and return the final string
    #     return "\n".join(result)

    def prepare_status_assistance_input(self, workflow_dict, step_no, error_dict = None):
        # Initialize the formatted result string
        result = []
        
        # Extract panel description
        panel_data = workflow_dict[str(self.panel_no)]
        panel_description = panel_data["panel_description"]
        
        # Workflow details
        result.append("Workflow:")
        result.append(f"Panel Description: {panel_description}")
        result.append("\nWorkflow Steps:")
        
        # Iterate through each step and build the formatted input
        steps = panel_data["steps"]
        for step_key, step_data in steps.items():
            # if int(step_key) > step_no:
            #     break
            
            # Add step details
            result.append(f"\nStep {step_key}")
            result.append(f"- API: {step_data['api']}")
            result.append(f"- Handles: {step_data['handles']}")
            
            # Input Variables
            result.append("- Input Variables:")
            for input_var in step_data['input_vars']:
                result.append(f"  - Name: {input_var['name']}")
                result.append(f"    - Parameter: {input_var['parameter']}")
                result.append(f"    - Type: {input_var['type']}")
                result.append(f"    - Source: {input_var['source']}")
                result.append(f"    - Description: {input_var['description']}")
                result.append(f"    - Value: {input_var.get('value', 'None')}")
            
            # Output Variables
            result.append("- Output Variables:")
            for output_var in step_data['output_vars']:
                result.append(f"  - Name: {output_var['name']}")
                result.append(f"    - Description: {output_var['description']}")
        
        # Add Current API Step
        result.append(f"\nCurrent API Step: Panel {self.panel_no}, Step {step_no}")
        
        # Add Previous Status Update (if exists)
        previous_update_str = "\nPrevious Status Update:\n"
        
        if self.prev_status_update:
            previous_update_str += self.prev_status_update
        
        result.append(previous_update_str)

        # Add Assistance Request Needed section if error_dict is provided
        if error_dict:
            assistance_request_str = "\nAssistance Request Needed, Error is:\n"
            assistance_request_str += f"{str(error_dict)}"
            result.append(assistance_request_str)

        # Join and return the final string
        return "\n".join(result)
    

    # for making the string including the whole workflow with filled in values of the output variables. We send this for getting the user readable output
    def make_final_workflow_with_output_values(self, workflow_dict, panels_list):
        # Initialize the formatted result string
        result = []
        
        # Extract panel description
        panel_data = workflow_dict[str(self.panel_no)]
        panel_description = panel_data["panel_description"]
        
        # Workflow details
        result.append("Please make user readable output for this workflow:\n")
        result.append("Workflow:")
        result.append(f"Panel Description: {panel_description}")
        result.append(f"Panel Details: {panels_list[self.panel_no-1]['request']['description']}")
        result.append("\nWorkflow Steps:")
        
        # Iterate through each step and build the formatted input
        steps = panel_data["steps"]
        for step_key, step_data in steps.items():
            # if int(step_key) > step_no:
            #     break
            
            # Add step details
            result.append(f"\nStep {step_key}")
            result.append(f"- API: {step_data['api']}")
            result.append(f"- Handles: {step_data['handles']}")
            
            # Input Variables
            result.append("- Input Variables:")
            for input_var in step_data['input_vars']:
                result.append(f"  - Name: {input_var['name']}")
                result.append(f"    - Parameter: {input_var['parameter']}")
                result.append(f"    - Type: {input_var['type']}")
                result.append(f"    - Source: {input_var['source']}")
                result.append(f"    - Description: {input_var['description']}")
                result.append(f"    - Value: {input_var['value']}")
            
            # Output Variables
            result.append("- Output Variables:")
            for output_var in step_data['output_vars']:
                result.append(f"  - Name: {output_var['name']}")
                result.append(f"    - Description: {output_var['description']}")
                result.append(f"    - Value: {output_var['value']}")

        # Join and return the final string
        return "\n".join(result)

    
    ###################################################################
    # ALL THE PARSING FUNCTIONS WILL BE HERE

    # def parse_api_request(self, text):
    #     # Initialize the result dictionary
    #     result = {
    #         'chain_of_thought': '',
    #         'api_requests': []
    #     }
        
    #     # First, split the text by $$CHAIN_OF_THOUGHT$$
    #     cot_sections = re.split(r"\$\$CHAIN_OF_THOUGHT\$\$", text)
        
    #     if len(cot_sections) != 2:
    #         raise ValueError("The text must contain one $$CHAIN_OF_THOUGHT$$ section.")
        
    #     # cot_sections[0]: text before $$CHAIN_OF_THOUGHT$$ (likely empty)
    #     # cot_sections[1]: chain_of_thought and the rest
        
    #     # Now, from cot_sections[1], split off the chain_of_thought and the $$API_REQUEST$$ sections
    #     parts_after_cot = re.split(r"\$\$API_REQUEST\$\$", cot_sections[1])
        
    #     # The chain_of_thought is the first part
    #     result['chain_of_thought'] = parts_after_cot[0].strip()
        
    #     # The rest are the API_REQUEST sections
    #     api_request_sections = parts_after_cot[1:]

    #     api_request_error_bool = False
        
    #     # Process each API_REQUEST section
    #     for api_request_text in api_request_sections:
    #         api_request_text = api_request_text.strip()
            
    #         # Initialize a dictionary to hold the API request details
    #         api_request = {}
            
    #         # Check for error response
    #         if 'STATUS_CODE' in api_request_text and 'ERROR_EXPLANATION' in api_request_text:
    #             # Extract status code and error explanation
    #             status_match = re.search(r"STATUS_CODE\s+(\d+)\s+(.*)", api_request_text)
    #             error_match = re.search(r"ERROR_EXPLANATION\s*-\s*(.*)", api_request_text, re.DOTALL)
    #             if status_match and error_match:
    #                 api_request['status_code'] = int(status_match.group(1).strip())
    #                 api_request['status_text'] = status_match.group(2).strip()
    #                 api_request['error_explanation'] = error_match.group(1).strip()
    #                 api_request_error_bool = True
    #                 return api_request_error_bool, api_request
    #             else:
    #                 raise ValueError("Error response format is incorrect.")
    #         else:
    #             # Extract method and URL
    #             endpoint_match = re.search(
    #                 r"API_ENDPOINT\s+Method:\s*(GET|POST|PUT|PATCH|DELETE|FUNCTION)\s+URL:\s*(\S+)",
    #                 api_request_text
    #             )
    #             if endpoint_match:
    #                 api_request['method'] = endpoint_match.group(1).strip()
    #                 api_request['url'] = endpoint_match.group(2).strip()
    #             else:
    #                 raise ValueError("API_ENDPOINT section is missing or improperly formatted.")
                
    #             # If method is FUNCTION, set headers to empty
    #             if api_request['method'] == 'FUNCTION':
    #                 api_request['headers'] = {}
    #             else:
    #                 # Extract headers
    #                 headers_match = re.search(r"HEADERS\s*(\{\s*\}|\{.*?\})", api_request_text, re.DOTALL)
    #                 if headers_match:
    #                     headers_str = headers_match.group(1).strip()
    #                     try:
    #                         api_request['headers'] = json.loads(headers_str)
    #                     except json.JSONDecodeError:
    #                         api_request['headers'] = {}
    #                 else:
    #                     api_request['headers'] = {}
                
    #             # Extract body
    #             body_match = re.search(r"BODY\s*(\{\s*\}|\{.*?\})", api_request_text, re.DOTALL)
    #             if body_match:
    #                 body_str = body_match.group(1).strip()
    #                 try:
    #                     api_request['body'] = json.loads(body_str)
    #                 except json.JSONDecodeError:
    #                     api_request['body'] = {}
    #             else:
    #                 api_request['body'] = {}
            
    #         # Append the api_request to the result list
    #         result['api_requests'].append(api_request)
        
    #     return api_request_error_bool, result

    def parse_api_request(self, text):
        # Initialize the result dictionary
        result = {
            'chain_of_thought': '',
            'api_requests': []
        }
        
        # First, split the text by $$CHAIN_OF_THOUGHT$$
        cot_sections = re.split(r"\$\$CHAIN_OF_THOUGHT\$\$", text)
        
        if len(cot_sections) != 2:
            raise ValueError("The text must contain one $$CHAIN_OF_THOUGHT$$ section.")
        
        # cot_sections[0]: text before $$CHAIN_OF_THOUGHT$$ (likely empty)
        # cot_sections[1]: chain_of_thought and the rest
        
        # Now, from cot_sections[1], split off the chain_of_thought and the $$API_REQUEST$$ sections
        parts_after_cot = re.split(r"\$\$API_REQUEST\$\$", cot_sections[1])
        
        # The chain_of_thought is the first part
        result['chain_of_thought'] = parts_after_cot[0].strip()
        
        # The rest are the API_REQUEST sections
        api_request_sections = parts_after_cot[1:]

        api_request_error_bool = False
        
        # Process each API_REQUEST section
        for api_request_text in api_request_sections:
            api_request_text = api_request_text.strip()
            
            # Initialize a dictionary to hold the API request details
            api_request = {}
            
            if 'STATUS_CODE' in api_request_text and 'ERROR_EXPLANATION' in api_request_text:
                # Extract status code and error explanation with improved regex patterns
                status_match = re.search(
                    r"STATUS_CODE\s*[\r\n]+(\d+)\s+([A-Z_]+)",
                    api_request_text,
                    re.IGNORECASE
                )
                error_match = re.search(
                    r"ERROR_EXPLANATION\s*[\r\n]+([\s\S]+)",
                    api_request_text,
                    re.IGNORECASE
                )
                if status_match and error_match:
                    api_request['status_code'] = int(status_match.group(1).strip())
                    api_request['status_text'] = status_match.group(2).strip()
                    # Clean up the error explanation by removing any leading hyphens or bullets
                    error_explanation = error_match.group(1).strip()
                    error_explanation = re.sub(r'^[-\*\s]+', '', error_explanation, flags=re.MULTILINE)
                    api_request['error_explanation'] = error_explanation
                    api_request_error_bool = True
                    return api_request_error_bool, api_request
                else:
                    raise ValueError("Error response format is incorrect.")
            else:
                # Extract method and URL
                endpoint_match = re.search(
                    r"API_ENDPOINT\s+Method:\s*(GET|POST|PUT|PATCH|DELETE|FUNCTION)\s+URL:\s*(\S+)",
                    api_request_text
                )
                if endpoint_match:
                    api_request['method'] = endpoint_match.group(1).strip()
                    api_request['url'] = endpoint_match.group(2).strip()
                else:
                    raise ValueError("API_ENDPOINT section is missing or improperly formatted.")
                
                # Extract headers
                headers_match = re.search(r"HEADERS\s*(\{\s*\}|\{.*?\})?", api_request_text, re.DOTALL)
                if headers_match and headers_match.group(1):
                    headers_str = headers_match.group(1).strip()
                    try:
                        api_request['headers'] = json.loads(headers_str)
                    except json.JSONDecodeError:
                        api_request['headers'] = {}
                else:
                    api_request['headers'] = {}
                
                # Extract body
                body_match = re.search(r"BODY\s*(\{.*\})", api_request_text, re.DOTALL)
                if body_match:
                    body_str = body_match.group(1).strip()
                    try:
                        api_request['body'] = json.loads(body_str)
                    except json.JSONDecodeError:
                        api_request['body'] = {}
                else:
                    api_request['body'] = {}
            
            # Append the api_request to the result list
            result['api_requests'].append(api_request)
        
        return api_request_error_bool, result



    def parse_and_store_api_response(self, api_response_text, panel_no, step_no):
        # Split the text into CHAIN_OF_THOUGHT and API_RESPONSE sections
        sections = re.split(r"\$\$API_RESPONSE\$\$", api_response_text)
        if len(sections) != 2:
            raise ValueError("The text does not contain exactly one CHAIN_OF_THOUGHT and one API_RESPONSE section.")

        # Extract CHAIN_OF_THOUGHT section
        chain_of_thought_text = sections[0].strip()
        if not re.search(r"\$\$CHAIN_OF_THOUGHT\$\$", chain_of_thought_text):
            raise ValueError("CHAIN_OF_THOUGHT section not found or improperly formatted.")

        # Extract API_RESPONSE section
        api_response_text = sections[1].strip()

        # Parse the status code and status text
        match_status = re.search(r"Status_Code\s*\n\s*(\d+)\s*(.*)", api_response_text)
        if not match_status:
            raise ValueError("Status_Code section not found or improperly formatted.")
        
        status_code = int(match_status.group(1).strip())
        status_text = match_status.group(2).strip()

        current_panel_data = self.group_workflow[str(panel_no)]
        current_step_data = current_panel_data['steps'][str(step_no)]

        if status_code == 200 and status_text in ["OK", "Success"]:
            # Parse and validate the Output_Variables section
            match_output_vars = re.search(r"Output_Variables\s*(.*?)(?=\nDependent_Input_Variables|\nAPI Response|$)", api_response_text, re.DOTALL)
            if not match_output_vars:
                raise ValueError("Output_Variables section not found or improperly formatted.")
            
            output_vars_section = match_output_vars.group(1).strip()

            # Capture multiline content until the next variable or section
            output_vars = re.findall(r"- Variable Name: ([\w_]+)\s*- Content:\s*(.*?)(?=\n- Variable Name:|\nDependent_Input_Variables|\nAPI Response|$)", output_vars_section, re.DOTALL)
            if not output_vars:
                raise ValueError("No output variables found in the Output_Variables section.")

            # Store output variables and track the ones we've filled
            stored_output_vars = set()
            used_by_list = []

            for var_name, var_value in output_vars:
                found = False
                var_value = var_value.strip()  # Strip any trailing spaces or newlines

                for output_var in current_step_data['output_vars']:
                    if output_var['name'] == var_name:
                        output_var['value'] = var_value  # Store the output variable value exactly as is
                        stored_output_vars.add(var_name)  # Track which variables have been filled
                        used_by_list.extend(output_var['used_by'])  # Collect dependent panel/step info
                        found = True
                        break

                if not found:
                    raise ValueError(f"Output variable {var_name} is not expected in Panel {panel_no}, Step {step_no}.")

            # Ensure all output variables for the current step are filled
            expected_output_vars = {var['name'] for var in current_step_data['output_vars']}
            if stored_output_vars != expected_output_vars:
                missing_vars = expected_output_vars - stored_output_vars
                raise ValueError(f"Missing output variables for Panel {panel_no}, Step {step_no}: {', '.join(missing_vars)}")

            # Now process Dependent_Input_Variables
            match_dependent_vars = re.search(r"Dependent_Input_Variables\s*(.*?)(?=\nAPI Response|$)", api_response_text, re.DOTALL)
            if match_dependent_vars and len(used_by_list) > 0:
                dependent_vars_section = match_dependent_vars.group(1).strip()

                # Capture multiline content until the next variable or section
                dependent_vars = re.findall(r"- Variable Name: ([\w_]+)\s*- Panel: (\d+)\s*- Step: (\d+)\s*- Type: (\w+)\s*- Content:\s*(.*?)(?=\n- Variable Name:|\nAPI Response|$)", dependent_vars_section, re.DOTALL)
                if not dependent_vars:
                    raise ValueError("No dependent input variables found in the Dependent_Input_Variables section.")

                # Ensure each dependent variable is saved
                visited_dependencies = set()

                for dep_var_name, dep_panel_no, dep_step_no, dep_type, dep_content in dependent_vars:
                    dep_panel_no = str(dep_panel_no)
                    dep_step_no = str(dep_step_no)

                    # Check if the panel and step exist in the workflow dict
                    if dep_panel_no in self.group_workflow and dep_step_no in self.group_workflow[dep_panel_no]['steps']:
                        for input_var in self.group_workflow[dep_panel_no]['steps'][dep_step_no]['input_vars']:
                            if input_var['name'] == dep_var_name:
                                # Check if the type matches
                                if input_var['type'] != dep_type:
                                    raise ValueError(f"Type mismatch for {dep_var_name} in Panel {dep_panel_no}, Step {dep_step_no}. Expected {input_var['type']}, got {dep_type}.")
                                # Store the value exactly as is
                                input_var['value'] = dep_content.strip()
                                visited_dependencies.add((dep_panel_no, dep_step_no, dep_var_name))
                    else:
                        raise ValueError(f"Dependent variable {dep_var_name} not found in Panel {dep_panel_no}, Step {dep_step_no}.")

                # Ensure all expected dependent input variables have been assigned
                for use_idx in range(len(used_by_list)):
                    panel = used_by_list[use_idx]['panel']
                    step = used_by_list[use_idx]['step']
                    step_data = self.group_workflow[str(panel)]['steps'][str(step)]
                    for input_var in step_data['input_vars']:
                        if {"panel": panel_no, "step": step_no} in input_var['dependencies'] and input_var['value'] == "None":
                            raise ValueError(f"Input variable {input_var['name']} in Panel {panel}, Step {step} has not been assigned a value.")
            elif len(used_by_list) > 0:
                raise ValueError(f"Missing Dependent_Input_Variables for {panel_no}, Step {step_no}")
        else:
            # Handle error cases
            match_error = re.search(r"Error_Explanation\s*\n\s*(.*)", api_response_text, re.DOTALL)
            if not match_error:
                raise ValueError("Error_Explanation section not found for error response.")

            error_explanation = match_error.group(1).strip()
            return {
                'status_code': status_code,
                'status_text': status_text,
                'error_explanation': error_explanation
            }

        return self.group_workflow
    

    # def parse_status_assistance_input(self, input_str):
    #     # Initialize the result dictionary
    #     result = {
    #         'chain_of_thought': '',
    #         'status_update': {
    #             'previous_progress': '',
    #             'current_progress': '',
    #             'current_step': {},
    #             'completed_apis': [],
    #             'issues': '',
    #             'string': ''  # Store the full status update string
    #         },
    #         'assistance_request': None  # Initialize assistance request as None by default
    #     }

    #     # Split the input string into sections
    #     sections = re.split(r'\$\$CHAIN_OF_THOUGHT\$\$|\$\$STATUS_UPDATE\$\$|\$\$ASSISTANCE_REQUEST\$\$', input_str)

    #     if len(sections) < 3:
    #         raise ValueError("Input string must contain both $$CHAIN_OF_THOUGHT$$ and $$STATUS_UPDATE$$ sections.")

    #     # Parse the chain of thought section
    #     chain_of_thought = sections[1].strip()
    #     result['chain_of_thought'] = chain_of_thought

    #     # Parse the status update section
    #     status_update = sections[2].strip()
    #     result['status_update']['string'] = status_update  # Save the full status update string

    #     # Extract previous and current progress
    #     previous_progress_match = re.search(r"Previous Progress:\n(?:\s+-\s+)?(.*?)(?=\n\s+-\s+|\n-|\Z)", status_update, re.DOTALL)
    #     current_progress_match = re.search(r"Current Progress:\n(?:\s+-\s+)?(.*?)(?=\n\s+-\s+|\n-|\Z)", status_update, re.DOTALL)
    #     current_step_match = re.search(r"Current Step:\s*Panel\s*(\d+),\s*Step\s*(\d+)", status_update)
    #     issues_match = re.search(r"Encountered Issues:\n(?:\s+-\s+)?(.*)", status_update, re.DOTALL)

    #     # Assign extracted values
    #     result['status_update']['previous_progress'] = previous_progress_match.group(1).strip() if previous_progress_match else "None"
    #     result['status_update']['current_progress'] = current_progress_match.group(1).strip() if current_progress_match else ""
    #     result['status_update']['current_step'] = {
    #         'panel': int(current_step_match.group(1)) if current_step_match else None,
    #         'step': int(current_step_match.group(2)) if current_step_match else None
    #     }
    #     result['status_update']['issues'] = issues_match.group(1).strip() if issues_match else ""

    #     # Parse the completed APIs
    #     completed_apis_section_match = re.search(r"Completed APIs:\n(.*?)(?:\n- Encountered Issues:|\Z)", status_update, re.DOTALL)
    #     if completed_apis_section_match:
    #         apis_text = completed_apis_section_match.group(1)
    #         result['status_update']['completed_apis'] = self.parse_completed_apis(apis_text)

    #     # Check if any previously completed APIs are missing in the new status update
    #     if hasattr(self, 'prev_status_update') and self.prev_status_update:
    #         prev_completed_apis = {api['name'] for api in self.prev_status_update.get('completed_apis', [])}
    #         current_completed_apis = {api['name'] for api in result['status_update']['completed_apis']}

    #         print("prev_completed_apis : ",prev_completed_apis)
    #         print("current_completed_apis : ",current_completed_apis)
            
    #         missing_apis = prev_completed_apis - current_completed_apis
    #         if missing_apis:
    #             raise ValueError(f"Status update error: Missing previously completed APIs: {', '.join(missing_apis)}")

    #     # Parse the assistance request section if present
    #     if len(sections) >= 4:
    #         assistance_request = sections[3].strip()
    #         result['assistance_request'] = {'string': assistance_request}

    #         error_type_match = re.search(r"Error Type:\s+(\d{3})", assistance_request)
    #         error_step_match = re.search(r"Error Step:\s+Panel\s+(\d+),\s+Step\s+(\d+)", assistance_request)
    #         error_api_match = re.search(r"Error API:\s+(.*)", assistance_request)
    #         error_description_match = re.search(r"Error Description:\n(?:\s+-\s+)?(.*)", assistance_request, re.DOTALL)
    #         relevant_context_match = re.search(r"Relevant Context:\n(?:\s+-\s+)?(.*)", assistance_request, re.DOTALL)
    #         suggested_resolution_match = re.search(r"Suggested Resolution:\n(?:\s+-\s+)?(.*)", assistance_request, re.DOTALL)
            
    #         if error_type_match and error_type_match.group(1)[0] in ['4', '5', '6']:
    #             result['assistance_request'].update({
    #                 'error_type': error_type_match.group(1).strip(),
    #                 'error_step': {
    #                     'panel': int(error_step_match.group(1)) if error_step_match else None,
    #                     'step': int(error_step_match.group(2)) if error_step_match else None
    #                 },
    #                 'error_api': error_api_match.group(1).strip() if error_api_match else "",
    #                 'error_description': error_description_match.group(1).strip() if error_description_match else "",
    #                 'relevant_context': relevant_context_match.group(1).strip() if relevant_context_match else "",
    #                 'suggested_resolution': suggested_resolution_match.group(1).strip() if suggested_resolution_match else ""
    #             })
    #     else:
    #         result['assistance_request'] = None

    #     return result

    # def parse_completed_apis(self, apis_text):
    #     completed_apis = []
    #     current_api = None
    #     current_section = None
    #     lines = apis_text.strip().split('\n')
    #     for line in lines:
    #         stripped_line = line.strip()
    #         if re.match(r'^-\s+\S+:$', stripped_line):
    #             # New API name
    #             if current_api:
    #                 completed_apis.append(current_api)
    #             api_name = stripped_line.lstrip('- ').rstrip(':')
    #             current_api = {'name': api_name, 'purpose': '', 'accomplished': ''}
    #             current_section = None
    #         elif re.match(r'^-\s+Purpose:', stripped_line):
    #             # Purpose line
    #             purpose = stripped_line.lstrip('- Purpose:').strip()
    #             current_api['purpose'] = purpose
    #             current_section = 'purpose'
    #         elif re.match(r'^-\s+Accomplished:', stripped_line):
    #             # Accomplished section starts
    #             current_section = 'accomplished'
    #             current_api['accomplished'] = ''
    #         elif re.match(r'^-\s+.*', stripped_line):
    #             # Sub-item under Accomplished or multi-line Purpose
    #             content = stripped_line.lstrip('- ').strip()
    #             if current_section == 'accomplished':
    #                 if current_api['accomplished']:
    #                     current_api['accomplished'] += ' ' + content
    #                 else:
    #                     current_api['accomplished'] = content
    #             elif current_section == 'purpose':
    #                 current_api['purpose'] += ' ' + content
    #         else:
    #             # Continuation of previous section (multi-line)
    #             if current_section == 'accomplished':
    #                 current_api['accomplished'] += ' ' + stripped_line
    #             elif current_section == 'purpose':
    #                 current_api['purpose'] += ' ' + stripped_line
    #     if current_api:
    #         completed_apis.append(current_api)
    #     return completed_apis
            
    def parse_status_assistance_input(self, input_str):
        # Initialize the result dictionary
        result = {
            'chain_of_thought': '',
            'status_update': '',
            'assistance_request': None
        }

        # Split the input string into sections
        sections = re.split(r'\$\$CHAIN_OF_THOUGHT\$\$\s*', input_str)
        if len(sections) != 2:
            raise ValueError("The input must contain $$CHAIN_OF_THOUGHT$$ section.")
        chain_of_thought_and_rest = sections[1]

        sections = re.split(r'\$\$STATUS_UPDATE\$\$\s*', chain_of_thought_and_rest)
        if len(sections) != 2:
            raise ValueError("The input must contain $$STATUS_UPDATE$$ section.")
        result['chain_of_thought'] = sections[0].strip()
        status_update_and_rest = sections[1]

        sections = re.split(r'\$\$ASSISTANCE_REQUEST\$\$\s*', status_update_and_rest)
        result['status_update'] = sections[0].strip()
        if len(sections) == 2:
            result['assistance_request'] = sections[1].strip()
        else:
            result['assistance_request'] = None

        return result
            




    
    ###################################################################
    # based on the api request we call process the api endpoints here
    def requests_func(self, method, api_endpoint, header=None, body=None):
        # Determine the request method and make the API call
        if method == "GET":
            response = requests.get(api_endpoint, headers=header, params=body)  # `params` is used for query parameters in GET
        elif method == "POST":
            response = requests.post(api_endpoint, headers=header, json=body)  # `json` is used for JSON body
        elif method == "PUT":
            response = requests.put(api_endpoint, headers=header, json=body)
        elif method == "PATCH":
            response = requests.patch(api_endpoint, headers=header, json=body)
        elif method == "DELETE":
            response = requests.delete(api_endpoint, headers=header)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        # Check if the request was successful
        if response.status_code == 200:
            return True, response.json()  # Return the JSON response if status is 200
        else:
            # If the status code is not 200, return the error with the status code
            return False, {"error": f"Request failed with status code {response.status_code}", "status_code": response.status_code, "response": response.text}
    
    
    # for running functions
    def function_call(self, api_name, body = None):
        
        response = FUNCTION_APIS_FUNCTION_DICT[api_name](body)

        # Check if the request was successful
        if response["status_code"] == 200:
            return True, response["text"]  # Return the JSON response if status is 200
        else:
            # If the status code is not 200, return the error with the status code
            return False, {"error": "Request failed", "status_code": response['status_code'], "response": response['text']}
        
    ###################################################################
    def reset_chat_history(self):
        self.chat_history = []
        self.chat_history.append({"role": "system", "content": self.system_prompt})
        # prev_status_update will act like summary
        if self.prev_status_update:
            self.chat_history.append({"role": "user", "content": "Prev Status Update as Summary: " + self.prev_status_update})
        else:
            self.chat_history.append({"role": "user", "content": "Prev Status Update as Summary:\nNone"})

    def num_tokens_from_string(self, string, encoding_name = 'gpt-4'):
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    ###################################################################
    async def wait_for_response(self, timeout=600):
        start_time = time.time()
        while not (self.drop or self.modify):
            if time.time() - start_time > timeout:
                raise TimeoutError("Timeout waiting for MainTranslator response")
            await asyncio.sleep(0.1)
        

    ###################################################################
    async def build_verify(self):
        """
        This function goes through each step of the workflow and prepares inputs based on the workflow details
        and the API descriptions provided.
        
        Args:
            api_descriptions (dict): Dictionary where the key is the API name and the value is the API description.
        """
        overall_success_bool = False
        overall_counter = 0
        while not overall_success_bool and overall_counter < 5:
            # self.chat_history = []
            overall_counter += 1
            
            if not self.group_workflow:
                raise ValueError("No group workflow found for this panel.")
            if not self.panel_workflow:
                raise ValueError("No panel workflow found for this panel.")
            
            num_steps = len(self.panel_workflow)
            
            # preperation of input data for detailed workflow creation
            assistance_request_bool = False
            assistance_error_dict = None
            for s_i in range(num_steps):
                step_no = s_i+1
                step = self.panel_workflow[str(step_no)]
                api_outputs_list = []
                print(f"Processing Step {step_no} for API: {step['api']}")

                ###########
                # At the start of each step we will reset the self.chat_history
                print("\nself.chat_history : ",self.chat_history)
                self.reset_chat_history()
            
                ###########
                # API_RUNNING Part with Error Handling

                # Call the function to prepare the input for the current step
                if step['api'] in RAPID_APIS_DICT:
                    api_documentation = RAPID_APIS_DICT[step['api']]
                elif step['api'] in FUNCTION_APIS_DOCUMENTATION_DICT:
                    api_documentation = FUNCTION_APIS_DOCUMENTATION_DICT[step['api']]
                else:
                    raise ValueError("API Documentation Not Found.")
                input_data = self.prepare_input_for_api_running_step(step, api_documentation)
                # print(f"Prepared input for step {step['step']}: {input_data}")

                print("input_data : ",input_data)

                # generating the api request from the LLM
                self.chat_history.append({"role": "user", "content": self.api_running_prompt}) # system prompt for workflow_creation
                self.chat_history.append({"role": "user", "content": input_data})

                # running the llm and if the format is wrong then we will ask it to retry.
                run_success = False
                api_input_error_counter = 0
                api_running_error_counter = 0
                parse_error_bool = False
                api_success_bool = False
                while not run_success and api_input_error_counter < 5 and api_running_error_counter < 3:
                    # preparing the input to the api
                    api_input_error_counter += 1
                    try:
                        api_request_llm = self.generate()
                        print("api_request_llm : ",api_request_llm)
                        parse_error_bool, parsed_api_request = self.parse_api_request(api_request_llm)
                        if parse_error_bool:
                            # need to call main translator module for assistance
                            print("\nparsed_api_request : ",parsed_api_request)
                            assistance_request_bool = True
                            assistance_error_dict = parsed_api_request
                            break
                        print("parsed_api_request : ",parsed_api_request)
                        run_success = True
                    except Exception as e:
                        error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT and API_REQUEST without any other details before or after.:\n {str(e)}' 
                        self.chat_history.append({"role": "user", "content": error_message})
                        print("api input error_message : ",error_message)
                        continue

                    # running the api
                    api_running_error_counter += 1
                    try:
                        for api_req_i in range(len(parsed_api_request['api_requests'])):
                            if parsed_api_request['api_requests'][api_req_i]['method'] == "FUNCTION":
                                api_success_bool, api_output = self.function_call(step['api'], parsed_api_request['api_requests'][api_req_i]['body'])
                            else:
                                api_success_bool, api_output = self.requests_func(parsed_api_request['api_requests'][api_req_i]['method'], parsed_api_request['api_requests'][api_req_i]['url'], parsed_api_request['api_requests'][api_req_i]['headers'], parsed_api_request['api_requests'][api_req_i]['body'])

                            # if api_output is too big then we will summarize here itslef else it would take a lot of context
                            # _ = tiktoken.get_encoding("cl100k_base")
                            if len(str(api_output)) > 80000:
                                print("Earlier character length was more than 80000, to be precisely it was: ",len(str(api_output)))
                                api_output = str(api_output)[:80000]
                                print("After the length became: ", len(str(api_output)))
                            print("num of tokens : ",self.num_tokens_from_string(f"{api_output}"))
                            if self.num_tokens_from_string(f"{api_output}") > 10000:
                                llm_input_api_output_summarize = self.prepare_input_for_api_output_summarize(api_output, self.panel_no, step_no)
                                print("llm_input_api_output_summarize : ",llm_input_api_output_summarize)
                                self.chat_history.append({"role": "user", "content": llm_input_api_output_summarize })
                                llm_output_api_output_summarize = self.generate()
                                # remove the last two chat history
                                self.chat_history.pop()
                                self.chat_history.pop()
                                # assign llm_output_api_output_summarize to api_output
                                api_output = llm_output_api_output_summarize
                                print("after summarize num of tokens : ",self.num_tokens_from_string(f"{api_output}"))

                            # if its a 4xx error then we can retry as it is possible that llm made a wrong api request
                            if not api_success_bool: # and int(api_output["status_code"])/100 == 4:
                                # error handling part here
                                raise ValueError(f"api_output : {api_output}")
                            # apart from 4xx errors we should just call the main translator for assistance
                            if not api_success_bool:
                                assistance_request_bool = True
                                assistance_error_dict = api_output
                                break
                            
                            api_outputs_list.append(api_output)

                        run_success = True
                    except Exception as e:
                        error_message = f'There was an error while running the API, please rectify based on this error message, only output the CHAIN_OF_THOUGHT and API_REQUEST without any other details before or after. Carefully review the api call and its documentation to identify and then rectify it.:\n {str(e)}' 
                        self.chat_history.append({"role": "user", "content": error_message})
                        print("api running error_message : ",error_message)
                        api_outputs_list = []

                if assistance_request_bool:
                    break

                if not run_success:
                    raise ValueError("Something is going wrong with the llm or the parsing function or api running fucntion. It is not an expected kind of error.")
                    
                ###########
                # API_OUTPUT, API_OUTPUT_DEPENDENCY Part with Error Handling

                # give the api_output to LLM and ask it to first verify if it seems plausile for our expectations from the api, then save the relevant part in the right format
                # additionally the LLM Agent will check if the api output has enough information such that we can fulfil the input variable requirement for future steps which depend on its output, and retrieve the relevant information and save it in the right format
                # api_output_llm_input = self.prepare_input_for_api_output(api_outputs_list[0], self.panel_no, step_no)
                api_output_llm_input = self.prepare_input_for_api_output(api_outputs_list, self.panel_no, step_no)
                print("\napi_output_llm_input : ",api_output_llm_input)
                # generating the api response format from the LLM
                self.chat_history.append({"role": "user", "content": self.api_output_prompt}) # system prompt for workflow_creation
                self.chat_history.append({"role": "user", "content": api_output_llm_input })


                run_success = False
                counter = 0
                while not run_success and counter < 5:
                    counter += 1
                    try:
                        api_output_llm_output = self.generate()
                        print("\napi_output_llm_output : ",api_output_llm_output)
                        api_parsed_output = self.parse_and_store_api_response(api_output_llm_output, self.panel_no, step_no)
                        # if a 6xx error was raised then status_code key will be there in api_parsed_output
                        if 'status_code' in api_parsed_output:
                            # call for assistance request along with giving error description
                            assistance_request_bool =  True
                            assistance_error_dict = api_parsed_output
                            break
                        print("api_parsed_output : ",api_parsed_output)
                        run_success = True
                    except Exception as e:
                        error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT and API_RESPONSE without any other details before or after.:\n {str(e)}' 
                        self.chat_history.append({"role": "user", "content": error_message})
                        print("error_message : ",error_message)

                if assistance_request_bool:
                    break

            
                if not run_success:
                    raise ValueError("Something is going wrong with the llm or the parsing function in api_output. It is not an expected kind of error.")
                    

                with open(f"workflow_updated_{self.panel_no}.json", "w") as json_file:
                    json.dump(self.group_workflow, json_file, indent=4)


                # running status update part
                status_assist_input = self.prepare_status_assistance_input(self.group_workflow, step_no)
                print("\nstatus_assist_input : ",status_assist_input)
                
                self.chat_history.append({"role": "user", "content": self.status_assistance_prompt}) # system prompt for workflow_creation
                self.chat_history.append({"role": "user", "content": status_assist_input}) # system prompt for workflow_creation

                run_success = False
                counter = 0
                while not run_success and counter < 5:
                    counter += 1
                    try:
                        status_update = self.generate()
                        print("\nstatus_update : ",status_update)
                        parsed_status_update = self.parse_status_assistance_input(status_update)
                        print("\parsed_status_update : ",parsed_status_update)
                        run_success = True
                    except Exception as e:
                        error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT and STATUS_UPDATE without any other details before or after.:\n {str(e)}' 
                        self.chat_history.append({"role": "user", "content": error_message})
                        print("error_message : ",error_message)
                
                if not run_success:
                    raise ValueError("Something is going wrong with the llm or the parsing function in status_update send without assistance request. It is not an expected kind of error.")
                
                # updating the prev_status_update
                self.prev_status_update = parsed_status_update['status_update']

            
            if assistance_request_bool:
                status_assist_input = self.prepare_status_assistance_input(self.group_workflow, step_no, assistance_error_dict)
                print("\nstatus_assist_input : ",status_assist_input)
                self.chat_history.append({"role": "user", "content": self.status_assistance_prompt}) # system prompt for workflow_creation
                self.chat_history.append({"role": "user", "content": status_assist_input}) # system prompt for workflow_creation

                run_success = False
                counter = 0
                while not run_success and counter < 5:
                    counter += 1
                    try:
                        status_update = self.generate()
                        print("\nstatus_update : ",status_update)
                        parsed_status_update = self.parse_status_assistance_input(status_update)
                        print("\parsed_status_update : ",parsed_status_update)
                        run_success = True
                    except Exception as e:
                        error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT, STATUS_UPDATE and ASSISTANCE_REQUEST without any other details before or after.:\n {str(e)}' 
                        self.chat_history.append({"role": "user", "content": error_message})
                        print("error_message : ",error_message)
                
                if not run_success:
                    raise ValueError("Something is going wrong with the llm or the parsing function in status_update send with assistance request. It is not an expected kind of error.")

                await self.main_translator.communicate(parsed_status_update, self.panel_no, self)
                print("\nafter self.main_translator.communicate(parsed_status_update, self.panel_no, self)")
                try:
                    await self.wait_for_response()
                except TimeoutError:
                    print(f"Timeout waiting for response from MainTranslator for panel {self.panel_no}")
                    return None
                
                print("after try and timeout")

                if self.drop:
                    return None
                if self.modify:
                    return None
                
                await asyncio.sleep(0.2)
                continue
            else:
                # overall this step was succesful
                overall_success_bool = True

        if not overall_success_bool:
            raise ValueError(f"Overall the workflow failed for {self.panel_no}")
        
    def get_results(self):
        if self.drop:
            return {
            'panel_description' : self.panel_description,
            'output' : 'This Panel Was Dropped'
        }

        final_workflow_with_values = self.make_final_workflow_with_output_values(self.group_workflow, self.main_translator.panels_list)
        self.chat_history.append({"role": "user", "content": self.user_readable_output_prompt})
        self.chat_history.append({"role": "user", "content": final_workflow_with_values})
        output = self.generate()
        print("output.split('$$FORMATTED_OUTPUT$$')[-1] : ", output.split('$$FORMATTED_OUTPUT$$')[-1])
        return {
            'panel_description' : self.panel_description,
            'output' : output.split('$$FORMATTED_OUTPUT$$')[-1]
        }

            
    async def run_in_thread(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.build_verify)