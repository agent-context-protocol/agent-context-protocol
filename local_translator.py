from base import BaseNode
from available_apis.hardcoded_format.return_dict import HARDCODED_APIS_DICT
from available_apis.openapi_format.return_dict import OPEN_APIS_DICT
from available_apis.function_format.perplexity_function import perplexity_api_response
import json
import requests
import re

class LocalTranslatorNode(BaseNode):
    def __init__(self, panel_no, panel_description, system_prompt=None):
        super().__init__(panel_no, system_prompt)
        self.panel_no = panel_no
        self.panel_description = panel_description
        self.group_workflow = None
        self.panel_workflow = None

        self.get_system_prompts()
        self.get_api_keys()

    def get_system_prompts(self):
        # api_running_prompt
        with open('prompts/local_translator/api_running_prompt.txt', 'r') as file:
            self.api_running_prompt = file.read()
        
        # api_output_prompt
        with open('prompts/local_translator/api_output_prompt.txt', 'r') as file:
            self.api_output_prompt = file.read()

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
        result_str += f"\nAPI Response:\n\n{api_response}\n"
        
        return result_str
    
    ###################################################################
    # ALL THE PARSING FUNCTIONS WILL BE HERE

    def parse_api_request(self, text):
        # Split the text into CHAIN_OF_THOUGHT and multiple API_REQUEST sections
        sections = re.split(r"\$\$API_REQUEST\$\$", text)
        if len(sections) < 2:
            raise ValueError("The text does not contain at least one CHAIN_OF_THOUGHT and one API_REQUEST section.")

        # The first part is the CHAIN_OF_THOUGHT
        chain_of_thought_text = sections[0].strip()

        # Extract CHAIN_OF_THOUGHT as a single string
        match_chain_of_thought = re.search(r"\$\$CHAIN_OF_THOUGHT\$\$(.*)", chain_of_thought_text, re.DOTALL)
        if match_chain_of_thought:
            chain_of_thought = match_chain_of_thought.group(1).strip()
        else:
            raise ValueError("CHAIN_OF_THOUGHT section not found or improperly formatted.")

        # Process all API_REQUEST sections
        api_requests = []
        for api_request_text in sections[1:]:
            api_request_text = api_request_text.strip()

            # Parse each API_REQUEST details
            match_api_request = re.search(
                r"API_ENDPOINT\s+Method:\s*(GET|POST|PUT|PATCH|DELETE)\s+URL:\s*(\S+)\s+HEADERS\s*\{(.*?)\}\s+BODY\s*(\{(.*?)\})?",
                api_request_text,
                re.DOTALL
            )
            if match_api_request:
                method = match_api_request.group(1).strip()
                url = match_api_request.group(2).strip()
                headers = match_api_request.group(3).strip()
                body = match_api_request.group(5) if match_api_request.group(5) else "{}"
            else:
                raise ValueError("API_REQUEST section not found or improperly formatted.")

            # Validation: Ensure the method is valid
            valid_methods = ["GET", "PUT", "POST", "PATCH", "DELETE"]
            if method not in valid_methods:
                raise ValueError(f"Invalid method: {method}. Allowed methods are {valid_methods}.")

            # Parse Headers as a single dictionary
            headers_dict = {}
            if headers:
                # Remove extra quotes and parse headers into a dictionary
                header_blocks = re.findall(r'(["\']?)(.*?)(["\']?):\s*(["\']?)(.*?)(["\']?)$', headers, re.MULTILINE)
                for header in header_blocks:
                    key = header[1].strip().strip('"').strip("'")
                    value = header[4].strip().strip('"').strip("'")
                    headers_dict[key] = value

            # Parse the Body (if present and non-empty)
            body_dict = {}
            if body and body.strip() != "{}":
                try:
                    # Use json.loads for safer parsing if body is in JSON format
                    body_dict = json.loads(body)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Body is not in a valid JSON format: {e}")

            # Append the parsed API request to the list
            api_requests.append({
                'method': method,
                'url': url,
                'headers': headers_dict,  # Now it's a dictionary
                'body': body_dict
            })

        # Return the parsed structure with the list of API requests
        return {
            'chain_of_thought': chain_of_thought,  # Store chain of thought as a string
            'api_requests': api_requests  # List of dictionaries, one for each API request
        }


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

            # Parse each output variable and store it in the current step's output variables
            output_vars = re.findall(r"- Variable Name: ([\w_]+)\s*- Content: (.*)", output_vars_section)
            if not output_vars:
                raise ValueError("No output variables found in the Output_Variables section.")

            # Store output variables and track the ones we've filled
            stored_output_vars = set()
            used_by_list = []

            for var_name, var_value in output_vars:
                found = False
                for output_var in current_step_data['output_vars']:
                    if output_var['name'] == var_name:
                        output_var['value'] = var_value  # Store the output variable value
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
            if match_dependent_vars:
                dependent_vars_section = match_dependent_vars.group(1).strip()

                # Parse each dependent variable
                dependent_vars = re.findall(r"- Variable Name: ([\w_]+)\s*- Panel: (\d+)\s*- Step: (\d+)\s*- Type: (\w+)\s*- Content: (.*)", dependent_vars_section)
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
                                # Store the value
                                input_var['value'] = dep_content
                                visited_dependencies.add((dep_panel_no, dep_step_no, dep_var_name))
                    else:
                        raise ValueError(f"Dependent variable {dep_var_name} not found in Panel {dep_panel_no}, Step {dep_step_no}.")

                # Ensure all expected dependent input variables have been assigned
                print("used_by_list : ",used_by_list)
                for use_idx in range(len(used_by_list)):
                    panel = used_by_list[use_idx]['panel']
                    step = used_by_list[use_idx]['step']
                    print("panel : ",panel)
                    print("step : ",step)
                    step_data = self.group_workflow[str(panel)]['steps'][str(step)]
                    for input_var in step_data['input_vars']:
                        if {"panel": panel_no, "step": step_no} in input_var['dependencies'] and input_var['value'] == "None":
                            raise ValueError(f"Input variable {input_var['name']} in Panel {panel}, Step {step} has not been assigned a value.")

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
                return True, response.json()  # Return the JSON response if status is 200
            else:
                # If the status code is not 200, return the error with the status code
                return False, {"error": f"Request failed with status code {response.status_code}", "response": response.text}
        
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
        if not self.group_workflow:
            raise ValueError("No group workflow found for this panel.")
        if not self.panel_workflow:
            raise ValueError("No panel workflow found for this panel.")
        
        num_steps = len(self.panel_workflow)
        
        # preperation of input data for detailed workflow creation
        input_data_list = []
        api_output = None
        for s_i in range(num_steps):
            step_no = s_i+1
            step = self.panel_workflow[str(step_no)]
            api_outputs_list = []
            print(f"Processing Step {step_no} for API: {step['api']}")
            # if api is perplexity/plot agent/text to image then we will use hardcoded
            if step['api'] in ["Perplexity", "PlotAgent", "TextToImage"]:
                if step['api'] == "Perplexity":
                    if len(step['input_vars']) != 1:
                        raise ValueError("With perplexity api we ony expected a single input variable.")
                    api_output = perplexity_api_response(step['input_vars'][0]['value'])
                    api_outputs_list.append(api_output)
            else:
                ###########
                # API_RUNNING Part with Error Handling

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

                # generating the api request from the LLM
                self.chat_history.append({"role": "system", "content": self.api_running_prompt}) # system prompt for workflow_creation
                self.chat_history.append({"role": "user", "content": input_data})

                # running the llm and if the format is wrong then we will ask it to retry.
                run_success = False
                counter = 0
                while not run_success and counter < 5:
                    try:
                        api_request_llm = self.generate()
                        print("api_request_llm : ",api_request_llm)
                        # print(cause_error)
                        parsed_api_request = self.parse_api_request(api_request_llm)
                        print("parsed_api_request : ",parsed_api_request)
                        run_success = True
                    except Exception as e:
                        error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT and API_REQUEST without any other details before or after.:\n {str(e)}' 
                        self.chat_history.append({"role": "user", "content": error_message})
                        print("error_message : ",error_message)
                    
                    counter += 1

                for api_req_i in range(len(parsed_api_request['api_requests'])):
                    api_success_bool, api_output = self.requests_func(parsed_api_request['api_requests'][api_req_i]['method'], parsed_api_request['api_requests'][api_req_i]['url'], parsed_api_request['api_requests'][api_req_i]['headers'], parsed_api_request['api_requests'][api_req_i]['body'])
                    if not api_success_bool:
                        # error handling part here
                        raise NotImplementedError

                    api_outputs_list.append(api_output)
                
            ###########
            # API_OUTPUT, API_OUTPUT_DEPENDENCY Part with Error Handling
            print("api_output : ",api_output)

            # give the api_output to LLM and ask it to first verify if it seems plausile for our expectations from the api, then save the relevant part in the right format
            # additionally the LLM Agent will check if the api output has enough information such that we can fulfil the input variable requirement for future steps which depend on its output, and retrieve the relevant information and save it in the right format
            api_output_llm_input = self.prepare_input_for_api_output(api_outputs_list[0], self.panel_no, step_no)
            print("\napi_output_llm_input : ",api_output_llm_input)
            # generating the api response format from the LLM
            self.chat_history.append({"role": "system", "content": self.api_output_prompt}) # system prompt for workflow_creation
            self.chat_history.append({"role": "user", "content": api_output_llm_input })
            api_output_llm_output = self.generate()
            print("\napi_output_llm_output : ",api_output_llm_output)


            api_parsed_output = self.parse_and_store_api_response(api_output_llm_output, self.panel_no, step_no)

            print("api_parsed_output : ",api_parsed_output)

            with open("workflow_updated.json", "w") as json_file:
                json.dump(api_parsed_output, json_file, indent=4)

            
            break
            
