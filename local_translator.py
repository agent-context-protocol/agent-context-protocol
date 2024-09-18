from base import BaseNode
from available_apis.hardcoded_format.return_dict import HARDCODED_APIS_DICT
from available_apis.openapi_format.return_dict import OPEN_APIS_DICT
from available_apis.function_format.perplexity_function import perplexity_api_response
import json
import requests
import re

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

        # Add the API documentation provided
        input_string += "\nAPI Documentation:\n"
        input_string += api_documentation

        return input_string
    
    ###################################################################
    # ALL THE PARSING FUNCTIONS WILL BE HERE

    def parse_api_request(self, text):
        # Split the text into CHAIN_OF_THOUGHT and API_REQUEST sections
        sections = re.split(r"\$\$API_REQUEST\$\$", text)
        if len(sections) != 2:
            raise ValueError("The text does not contain exactly one CHAIN_OF_THOUGHT and one API_REQUEST section.")

        chain_of_thought_text = sections[0].strip()
        api_request_text = sections[1].strip()

        # Extract CHAIN_OF_THOUGHT as a single string
        match_chain_of_thought = re.search(r"\$\$CHAIN_OF_THOUGHT\$\$(.*)", chain_of_thought_text, re.DOTALL)
        if match_chain_of_thought:
            chain_of_thought = match_chain_of_thought.group(1).strip()
        else:
            raise ValueError("CHAIN_OF_THOUGHT section not found or improperly formatted.")

        # Parse API_REQUEST details
        match_api_request = re.search(
            r"API_ENDPOINT\s+Method:\s*(GET|POST|PUT|PATCH|DELETE)\s+URL:\s*(\S+)\s+HEADERS\s*(.*?)\s+BODY\s*(.*)",
            api_request_text,
            re.DOTALL
        )
        if match_api_request:
            method = match_api_request.group(1).strip()
            url = match_api_request.group(2).strip()
            headers = match_api_request.group(3).strip()
            body = match_api_request.group(4).strip()
        else:
            raise ValueError("API_REQUEST section not found or improperly formatted.")

        # Validation: Ensure the method is valid
        valid_methods = ["GET", "PUT", "POST", "PATCH", "DELETE"]
        if method not in valid_methods:
            raise ValueError(f"Invalid method: {method}. Allowed methods are {valid_methods}.")

        # Parse Headers (if any)
        headers_list = []
        if headers:
            header_blocks = re.findall(r"(.*?):\s*(.*?)$", headers, re.MULTILINE)
            for header in header_blocks:
                headers_list.append({'name': header[0].strip(), 'value': header[1].strip()})

        # Parse the Body (if present)
        if body and body != "BODY":
            try:
                body_dict = eval(body) if body.strip() else {}
            except Exception as e:
                raise ValueError(f"Body is not in a valid format: {e}")
        else:
            body_dict = {}

        # Return the parsed structure
        return {
            'chain_of_thought': chain_of_thought,  # Store chain of thought as a string
            'api_request': {
                'method': method,
                'url': url,
                'headers': headers_list,
                'body': body_dict
            }
        }
    
    ###################################################################
    # based on the api request we call process the api endpoints here
    def requests_func(self, method, api_endpoint, header=None, body=None):
        try:
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
                return response.json()  # Return the JSON response if status is 200
            else:
                # If the status code is not 200, return the error with the status code
                return {"error": f"Request failed with status code {response.status_code}", "response": response.text}
        
        except requests.RequestException as e:
            # Handle any requests exceptions such as network issues
            return {"error": f"An error occurred: {str(e)}"}


    ###################################################################
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
        api_output = None
        for s_i in range(num_steps):
            step = self.workflow[str(s_i+1)]
            print(f"Processing Step {s_i+1} for API: {step['api']}")
            # if api is perplexity/plot agent/text to image then we will use hardcoded
            if step['api'] in ["Perplexity", "PlotAgent", "TextToImage"]:
                if step['api'] == "Perplexity":
                    if len(step['input_vars']) != 1:
                        raise ValueError("With perplexity api we ony expected a single input variable.")
                    api_output = perplexity_api_response(step['input_vars'][0]['value'])
            else:
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

                print("input_data : ",input_data)

                # generating the workflow from the LLM
                self.chat_history.append({"role": "system", "content": self.workflow_finalization_prompt}) # system prompt for workflow_creation
                self.chat_history.append({"role": "user", "content": input_data})

                api_request_llm = self.generate()
                print("api_request_llm : ",api_request_llm)
                # print(cause_error)

                parsed_api_request = self.parse_api_request(api_request_llm)
                print("parsed_api_request : ",parsed_api_request)

                api_output = self.requests_func(parsed_api_request['api_request']['method'], parsed_api_request['api_request']['url'], parsed_api_request['api_request']['headers'], parsed_api_request['api_request']['body'])

            print("api_output : ",api_output)
            break
            
