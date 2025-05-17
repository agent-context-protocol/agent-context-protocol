from .base import BaseNode
from .available_tools.hardcoded_format.return_dict import HARDCODED_TOOLS_DICT
from .available_tools.openapi_format.return_dict import OPENAPI_TOOLS_DICT
from .available_tools.function_format.return_dict import FUNCTION_TOOLS_DOCUMENTATION_DICT, FUNCTION_TOOLS_FUNCTION_DICT
from .available_tools.rapid_apis_format.return_dict import RAPIDAPI_TOOLS_DICT
import json
import requests
import re
import asyncio
import time
import tiktoken
from importlib import resources
import agent_context_protocol.prompts.agent as agent_prompts
import agent_context_protocol.external_env_details as env_details

class AgentNode(BaseNode):
    def __init__(self, sub_task_no, sub_task_description, system_prompt=None, dag_compiler=None):
        super().__init__(sub_task_no, system_prompt)
        self.sub_task_no = sub_task_no
        self.sub_task_description = sub_task_description
        self.group_execution_blueprint = None
        self.sub_task_execution_blueprint = None
        self.dag_compiler = dag_compiler
        self.group_id = None

        self.prev_status_update = None

        self.get_system_prompts()
        self.get_tool_keys()

        self.drop = False
        self.modify = False

    def get_system_prompts(self):
        with resources.open_text(agent_prompts, "agent_request_prompt.txt") as file:
            self.agent_request_prompt = file.read()

        with resources.open_text(agent_prompts, "agent_response_prompt.txt") as file:
            self.agent_response_prompt = file.read()

        with resources.open_text(agent_prompts, "status_assistance_prompt.txt") as file:
            self.status_assistance_prompt = file.read()

        with resources.open_text(agent_prompts, "user_readable_output_prompt.txt") as file:
            self.user_readable_output_prompt = file.read()

        with resources.open_text(agent_prompts, "tool_output_summarizer_prompt.txt") as file:
            self.tool_output_summarizer_prompt = file.read()

    def get_tool_keys(self):
        with resources.open_text(env_details, "tool_keys.json") as json_file:
            self.tool_keys = json.load(json_file)

    ###################################################################
    # input format prep functions

    def prepare_input_for_tool_running_step(self, step, tool_documentation):
        """
        Prepare the input for a single step in the execution_blueprint.
        
        Args:
            step (dict): The execution_blueprint step that contains the tool details, input vars, output vars, etc.
            tool_description (dict): The tool description (loaded from a dictionary based on tool name).
            
        Returns:
            dict: The prepared input data for the tool request.
        """
        input_string = "\nPlease generate output for this input:\n"
        input_string += "Step Details:\n"

        input_string += f"- Tool: {step['tool']}\n"
        input_string += f"- Handles: {step['handles']}\n"
        
        input_string += "- Input Variables:\n"
        for var in step['input_vars']:
            input_string += f"  - Name: {var['name']}\n"
            input_string += f"    - Parameter: {var['parameter']}\n"
            input_string += f"    - Type: {var['type']}\n"
            input_string += f"    - Source: {var['source']}\n"
            input_string += f"    - Description: {var['description']}\n"
            input_string += f"    - Value: \"{var['value']}\"\n"

        input_string += "- Output Variables:\n"
        for var in step['output_vars']:
            input_string += f"  - Name: {var['name']}\n"
            input_string += f"    - Description: {var['description']}\n"

        if step['tool'] in self.tool_keys:
            input_string += "\nAdditonal Input Details:\n"
            input_string += f"TOOL_KEY: {self.tool_keys[step['tool']]}\n"
        elif step['tool'] in RAPIDAPI_TOOLS_DICT:
            input_string += "\nAdditonal Input Details:\n"
            rapidapi_tool_key = self.tool_keys["Rapid_API_Key"]
            input_string += f"TOOL_KEY: {rapidapi_tool_key}\n"

        input_string += "\nTOOL Documentation:\n"
        input_string += tool_documentation

        return input_string
    
    def prepare_input_for_tool_output(self, tool_response, sub_task_no, step_no):
        result_str = ""

        print(self.group_execution_blueprint)
        sub_task_data = self.group_execution_blueprint[str(sub_task_no)]
        step_data = sub_task_data['steps'][str(step_no)]

        tool_name = step_data['tool']
        handles = step_data['handles']

        result_str += f"Current Step Details:\n\n- tool: {tool_name}\n- Handles: {handles}\n"

        result_str += "- Input Variables:\n"
        for input_var in step_data['input_vars']:
            result_str += f"  - Name: {input_var['name']}\n"
            result_str += f"    - Parameter: {input_var['parameter']}\n"
            result_str += f"    - Type: {input_var['type']}\n"
            result_str += f"    - Source: {input_var['source']}\n"
            result_str += f"    - Description: {input_var['description']}\n"
            result_str += f"    - Value: \"{input_var['value']}\"\n"

        result_str += "- Output Variables:\n"
        for output_var in step_data['output_vars']:
            result_str += f"  - Name: {output_var['name']}\n"
            result_str += f"    - Description: {output_var['description']}\n"

        has_dependent_steps = False
        visited_sub_task_steps = []
        for output_var in step_data['output_vars']:
            if output_var['used_by']:
                if not has_dependent_steps:
                    result_str += f"\nDependent Input Variables Step Details:\n"
                    has_dependent_steps = True

                for dependent in output_var['used_by']:
                    dependent_sub_task_no = dependent['sub_task']
                    dependent_step_no = dependent['step']
                    if [dependent_sub_task_no, dependent_step_no] in visited_sub_task_steps:
                        continue
                    visited_sub_task_steps.append([dependent_sub_task_no, dependent_step_no])
                    
                    dependent_sub_task_data = self.group_execution_blueprint[str(dependent_sub_task_no)]
                    dependent_step_data = dependent_sub_task_data['steps'][str(dependent_step_no)]

                    result_str += f"\nsub_task {dependent_sub_task_no}, Step {dependent_step_no}:\n"
                    result_str += f"- TOOL: {dependent_step_data['tool']}\n"
                    result_str += f"- Handles: {dependent_step_data['handles']}\n"
                    result_str += "- Input Variables:\n"

                    for dep_input_var in dependent_step_data['input_vars']:
                        result_str += f"  - Name: {dep_input_var['name']}\n"
                        result_str += f"    - Parameter: {dep_input_var['parameter']}\n"
                        result_str += f"    - Type: {dep_input_var['type']}\n"
                        result_str += f"    - Source: {dep_input_var['source']}\n"
                        result_str += f"    - Description: {dep_input_var['description']}\n"
                        result_str += f"    - Value: {dep_input_var['value']}\n"

        for tool_ind, tool_resp in enumerate(tool_response):
            result_str += f"\nTOOL Response {tool_ind}:\n\n{tool_resp}\n"
        
        return result_str
    
    def prepare_input_for_tool_output_summarize(self, tool_response, sub_task_no, step_no):
        result_str = f"{self.tool_output_summarizer_prompt}"

        sub_task_data = self.group_execution_blueprint[str(sub_task_no)]
        step_data = sub_task_data['steps'][str(step_no)]

        has_dependent_steps = False
        visited_sub_task_steps = []
        for output_var in step_data['output_vars']:
            if output_var['used_by']:
                if not has_dependent_steps:
                    result_str += f"\nDependent Input Variables Step Details:\n"
                    has_dependent_steps = True

                for dependent in output_var['used_by']:
                    dependent_sub_task_no = dependent['sub_task']
                    dependent_step_no = dependent['step']
                    if [dependent_sub_task_no, dependent_step_no] in visited_sub_task_steps:
                        continue
                    visited_sub_task_steps.append([dependent_sub_task_no, dependent_step_no])
                    
                    dependent_sub_task_data = self.group_execution_blueprint[str(dependent_sub_task_no)]
                    dependent_step_data = dependent_sub_task_data['steps'][str(dependent_step_no)]

                    result_str += f"\nsub_task {dependent_sub_task_no}, Step {dependent_step_no}:\n"
                    result_str += f"- TOOL: {dependent_step_data['tool']}\n"
                    result_str += f"- Handles: {dependent_step_data['handles']}\n"
                    result_str += "- Input Variables:\n"

                    for dep_input_var in dependent_step_data['input_vars']:
                        result_str += f"  - Name: {dep_input_var['name']}\n"
                        result_str += f"    - Parameter: {dep_input_var['parameter']}\n"
                        result_str += f"    - Type: {dep_input_var['type']}\n"
                        result_str += f"    - Source: {dep_input_var['source']}\n"
                        result_str += f"    - Description: {dep_input_var['description']}\n"
                        result_str += f"    - Value: {dep_input_var['value']}\n"

        result_str += f"\nTOOL Response :\n\n{tool_response}\n"
        
        return result_str

    def prepare_status_assistance_input(self, execution_blueprint_dict, step_no, error_dict = None):
        result = []
        
        sub_task_data = execution_blueprint_dict[str(self.sub_task_no)]
        sub_task_description = sub_task_data["subtask_description"]
        
        result.append("execution_blueprint:")
        result.append(f"sub_task Description: {sub_task_description}")
        result.append("\nexecution_blueprint Steps:")
        
        steps = sub_task_data["steps"]
        for step_key, step_data in steps.items():

            result.append(f"\nStep {step_key}")
            result.append(f"- TOOL: {step_data['tool']}")
            result.append(f"- Handles: {step_data['handles']}")
            
            result.append("- Input Variables:")
            for input_var in step_data['input_vars']:
                result.append(f"  - Name: {input_var['name']}")
                result.append(f"    - Parameter: {input_var['parameter']}")
                result.append(f"    - Type: {input_var['type']}")
                result.append(f"    - Source: {input_var['source']}")
                result.append(f"    - Description: {input_var['description']}")
                result.append(f"    - Value: {input_var.get('value', 'None')}")
            
            result.append("- Output Variables:")
            for output_var in step_data['output_vars']:
                result.append(f"  - Name: {output_var['name']}")
                result.append(f"    - Description: {output_var['description']}")
                result.append(f"    - Value: {output_var.get('value', 'None')}")
        
        result.append(f"\nCurrent tool Step: sub_task {self.sub_task_no}, Step {step_no}")
        
        previous_update_str = "\nPrevious Status Update:\n"
        
        if self.prev_status_update:
            previous_update_str += self.prev_status_update
        
        result.append(previous_update_str)

        if error_dict:
            assistance_request_str = "\nAssistance Request Needed, Error is:\n"
            assistance_request_str += f"{str(error_dict)}"
            result.append(assistance_request_str)

        return "\n".join(result)
    

    def make_final_execution_blueprint_with_output_values(self, execution_blueprint_dict, sub_tasks_list):
        result = []
        
        sub_task_data = execution_blueprint_dict[str(self.sub_task_no)]
        sub_task_description = sub_task_data["subtask_description"]
        
        result.append("Please make user readable output for this execution_blueprint:\n")
        result.append("execution_blueprint:")
        result.append(f"sub_task Description: {sub_task_description}")
        result.append(f"sub_task Details: {sub_tasks_list[self.sub_task_no-1]['request']['description']}")
        result.append("\nexecution_blueprint Steps:")
        
        steps = sub_task_data["steps"]
        for step_key, step_data in steps.items():

            result.append(f"\nStep {step_key}")
            result.append(f"- TOOL: {step_data['tool']}")
            result.append(f"- Handles: {step_data['handles']}")
            
            result.append("- Input Variables:")
            for input_var in step_data['input_vars']:
                result.append(f"  - Name: {input_var['name']}")
                result.append(f"    - Parameter: {input_var['parameter']}")
                result.append(f"    - Type: {input_var['type']}")
                result.append(f"    - Source: {input_var['source']}")
                result.append(f"    - Description: {input_var['description']}")
                result.append(f"    - Value: {input_var['value']}")
            
            result.append("- Output Variables:")
            for output_var in step_data['output_vars']:
                result.append(f"  - Name: {output_var['name']}")
                result.append(f"    - Description: {output_var['description']}")
                result.append(f"    - Value: {output_var.get('value', 'None')}")

        return "\n".join(result)
    
    ###################################################################
    # ALL THE PARSING FUNCTIONS WILL BE HERE

    def parse_agent_request(self, text):
        result = {
            'chain_of_thought': '',
            'agent_requests': []
        }
        
        cot_sections = re.split(r"\$\$CHAIN_OF_THOUGHT\$\$", text)
        
        if len(cot_sections) != 2:
            raise ValueError("The text must contain one $$CHAIN_OF_THOUGHT$$ section.")
        
        parts_after_cot = re.split(r"\$\$AGENT_REQUEST\$\$", cot_sections[1])
        
        result['chain_of_thought'] = parts_after_cot[0].strip()
        
        agent_request_sections = parts_after_cot[1:]

        agent_request_error_bool = False
        
        for agent_request_text in agent_request_sections:
            agent_request_text = agent_request_text.strip()
            
            agent_request = {}
            
            if 'STATUS_CODE' in agent_request_text and 'ERROR_EXPLANATION' in agent_request_text:
                status_match = re.search(
                    r"STATUS_CODE\s*[\r\n]+(\d+)\s+([A-Z_]+)",
                    agent_request_text,
                    re.IGNORECASE
                )
                error_match = re.search(
                    r"ERROR_EXPLANATION\s*[\r\n]+([\s\S]+)",
                    agent_request_text,
                    re.IGNORECASE
                )
                if status_match and error_match:
                    agent_request['status_code'] = int(status_match.group(1).strip())
                    agent_request['status_text'] = status_match.group(2).strip()
                    error_explanation = error_match.group(1).strip()
                    error_explanation = re.sub(r'^[-\*\s]+', '', error_explanation, flags=re.MULTILINE)
                    agent_request['error_explanation'] = error_explanation
                    agent_request_error_bool = True
                    return agent_request_error_bool, agent_request
                else:
                    raise ValueError("Error response format is incorrect.")
            else:
                # Extract method and URL
                endpoint_match = re.search(
                    r"TOOL_ENDPOINT\s+Method:\s*(GET|POST|PUT|PATCH|DELETE|FUNCTION)\s+URL:\s*(\S+)",
                    agent_request_text
                )
                if endpoint_match:
                    agent_request['method'] = endpoint_match.group(1).strip()
                    agent_request['url'] = endpoint_match.group(2).strip()
                else:
                    raise ValueError("TOOL_ENDPOINT section is missing or improperly formatted.")
                
                headers_match = re.search(r"HEADERS\s*(\{\s*\}|\{.*?\})?", agent_request_text, re.DOTALL)
                if headers_match and headers_match.group(1):
                    headers_str = headers_match.group(1).strip()
                    try:
                        agent_request['headers'] = json.loads(headers_str)
                    except json.JSONDecodeError:
                        agent_request['headers'] = {}
                else:
                    agent_request['headers'] = {}
                
                body_match = re.search(r"BODY\s*(\{.*\})", agent_request_text, re.DOTALL)
                if body_match:
                    body_str = body_match.group(1).strip()
                    try:
                        agent_request['body'] = json.loads(body_str)
                    except json.JSONDecodeError:
                        agent_request['body'] = {}
                else:
                    agent_request['body'] = {}
            
            result['agent_requests'].append(agent_request)
        
        return agent_request_error_bool, result



    def parse_and_store_agent_response(self, agent_response_text, sub_task_no, step_no):
        sections = re.split(r"\$\$AGENT_RESPONSE\$\$", agent_response_text)
        if len(sections) != 2:
            raise ValueError("The text does not contain exactly one CHAIN_OF_THOUGHT and one AGENT_RESPONSE section.")

        chain_of_thought_text = sections[0].strip()
        if not re.search(r"\$\$CHAIN_OF_THOUGHT\$\$", chain_of_thought_text):
            raise ValueError("CHAIN_OF_THOUGHT section not found or improperly formatted.")

        agent_response_text = sections[1].strip()

        match_status = re.search(r"Status_Code\s*\n\s*(\d+)\s*(.*)", agent_response_text)
        if not match_status:
            raise ValueError("Status_Code section not found or improperly formatted.")
        
        status_code = int(match_status.group(1).strip())
        status_text = match_status.group(2).strip()

        current_sub_task_data = self.group_execution_blueprint[str(sub_task_no)]
        current_step_data = current_sub_task_data['steps'][str(step_no)]

        if status_code == 200 and status_text in ["OK", "Success"]:
            match_output_vars = re.search(r"Output_Variables\s*(.*?)(?=\nDependent_Input_Variables|\nTOOL Response|$)", agent_response_text, re.DOTALL)
            if not match_output_vars:
                raise ValueError("Output_Variables section not found or improperly formatted.")
            
            output_vars_section = match_output_vars.group(1).strip()

            output_vars = re.findall(r"- Variable Name: ([\w_]+)\s*- Content:\s*(.*?)(?=\n- Variable Name:|\nDependent_Input_Variables|\nTOOL Response|$)", output_vars_section, re.DOTALL)
            if not output_vars:
                raise ValueError("No output variables found in the Output_Variables section.")

            stored_output_vars = set()
            used_by_list = []

            for var_name, var_value in output_vars:
                found = False
                var_value = var_value.strip()  

                for output_var in current_step_data['output_vars']:
                    if output_var['name'] == var_name:
                        output_var['value'] = var_value  
                        stored_output_vars.add(var_name)  
                        used_by_list.extend(output_var['used_by']) 
                        found = True
                        break

                if not found:
                    raise ValueError(f"Output variable {var_name} is not expected in sub_task {sub_task_no}, Step {step_no}.")

            expected_output_vars = {var['name'] for var in current_step_data['output_vars']}
            if stored_output_vars != expected_output_vars:
                missing_vars = expected_output_vars - stored_output_vars
                raise ValueError(f"Missing output variables for sub_task {sub_task_no}, Step {step_no}: {', '.join(missing_vars)}")

            match_dependent_vars = re.search(r"Dependent_Input_Variables\s*(.*?)(?=\nTOOL Response|$)", agent_response_text, re.DOTALL)
            if match_dependent_vars and len(used_by_list) > 0:
                dependent_vars_section = match_dependent_vars.group(1).strip()

                dependent_vars = re.findall(r"- Variable Name: ([\w_]+)\s*- sub_task: (\d+)\s*- Step: (\d+)\s*- Type: (\w+)\s*- Content:\s*(.*?)(?=\n- Variable Name:|\nTOOL Response|$)", dependent_vars_section, re.DOTALL)
                if not dependent_vars:
                    raise ValueError("No dependent input variables found in the Dependent_Input_Variables section.")

                visited_dependencies = set()

                for dep_var_name, dep_sub_task_no, dep_step_no, dep_type, dep_content in dependent_vars:
                    dep_sub_task_no = str(dep_sub_task_no)
                    dep_step_no = str(dep_step_no)

                    if dep_sub_task_no in self.group_execution_blueprint and dep_step_no in self.group_execution_blueprint[dep_sub_task_no]['steps']:
                        for input_var in self.group_execution_blueprint[dep_sub_task_no]['steps'][dep_step_no]['input_vars']:
                            if input_var['name'] == dep_var_name:
                                # Check if the type matches
                                if input_var['type'] != dep_type:
                                    raise ValueError(f"Type mismatch for {dep_var_name} in sub_task {dep_sub_task_no}, Step {dep_step_no}. Expected {input_var['type']}, got {dep_type}.")
                                # Store the value exactly as is
                                input_var['value'] = dep_content.strip()
                                visited_dependencies.add((dep_sub_task_no, dep_step_no, dep_var_name))
                    else:
                        raise ValueError(f"Dependent variable {dep_var_name} not found in sub_task {dep_sub_task_no}, Step {dep_step_no}.")

                for use_idx in range(len(used_by_list)):
                    sub_task = used_by_list[use_idx]['sub_task']
                    step = used_by_list[use_idx]['step']
                    step_data = self.group_execution_blueprint[str(sub_task)]['steps'][str(step)]
                    for input_var in step_data['input_vars']:
                        if {"sub_task": sub_task_no, "step": step_no} in input_var['dependencies'] and input_var['value'] == "None":
                            raise ValueError(f"Input variable {input_var['name']} in sub_task {sub_task}, Step {step} has not been assigned a value.")
            elif len(used_by_list) > 0:
                raise ValueError(f"Missing Dependent_Input_Variables for {sub_task_no}, Step {step_no}")
        else:
            match_error = re.search(r"Error_Explanation\s*\n\s*(.*)", agent_response_text, re.DOTALL)
            if not match_error:
                raise ValueError("Error_Explanation section not found for error response.")

            error_explanation = match_error.group(1).strip()
            return {
                'status_code': status_code,
                'status_text': status_text,
                'error_explanation': error_explanation
            }

        return self.group_execution_blueprint
    
            
    def parse_status_assistance_input(self, input_str):
        result = {
            'chain_of_thought': '',
            'status_update': '',
            'assistance_request': None
        }

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
    # based on the tool request we call process the tool endpoints here
    def requests_func(self, method, tool_endpoint, header=None, body=None):
        if method == "GET":
            response = requests.get(tool_endpoint, headers=header, params=body) 
        elif method == "POST":
            response = requests.post(tool_endpoint, headers=header, json=body)  
        elif method == "PUT":
            response = requests.put(tool_endpoint, headers=header, json=body)
        elif method == "PATCH":
            response = requests.patch(tool_endpoint, headers=header, json=body)
        elif method == "DELETE":
            response = requests.delete(tool_endpoint, headers=header)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code == 200:
            return True, response.json()  
        else:
            return False, {"error": f"Request failed with status code {response.status_code}", "status_code": response.status_code, "response": response.text}
    
    
    def function_call(self, tool_name, body = None):
        
        response = FUNCTION_TOOLS_FUNCTION_DICT[tool_name](body)

        if response["status_code"] == 200:
            return True, response["text"] 
        else:
            return False, {"error": "Request failed", "status_code": response['status_code'], "response": response['text']}
        
    ###################################################################
    def reset_chat_history(self):
        self.chat_history = []
        self.chat_history.append({"role": "system", "content": self.system_prompt})
        if self.prev_status_update:
            self.chat_history.append({"role": "user", "content": "Prev Status Update as Summary: " + self.prev_status_update})
        else:
            self.chat_history.append({"role": "user", "content": "Prev Status Update as Summary:\nNone"})

    def num_tokens_from_string(self, string, encoding_name = 'gpt-4'):
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    async def wait_for_response(self, timeout=600):
        start_time = time.time()
        while not (self.drop or self.modify):
            if time.time() - start_time > timeout:
                raise TimeoutError("Timeout waiting for DAG Compiler response")
            await asyncio.sleep(0.1)
        
    async def build_verify(self):
        overall_success_bool = False
        overall_counter = 0
        while not overall_success_bool and overall_counter < 5:
            overall_counter += 1
            
            if not self.group_execution_blueprint:
                raise ValueError("No group execution_blueprint found for this sub_task.")
            if not self.sub_task_execution_blueprint:
                raise ValueError("No sub_task execution_blueprint found for this sub_task.")
            
            num_steps = len(self.sub_task_execution_blueprint)
            
            assistance_request_bool = False
            assistance_error_dict = None
            for s_i in range(num_steps):
                step_no = s_i+1
                step = self.sub_task_execution_blueprint[str(step_no)]
                tool_outputs_list = []
                print(f"Processing Step {step_no} for tool: {step['tool']}")

                self.reset_chat_history()
            
                if step['tool'] in RAPIDAPI_TOOLS_DICT:
                    tool_documentation = RAPIDAPI_TOOLS_DICT[step['tool']]
                elif step['tool'] in FUNCTION_TOOLS_DOCUMENTATION_DICT:
                    tool_documentation = FUNCTION_TOOLS_DOCUMENTATION_DICT[step['tool']]
                elif step['tool'] in self.dag_compiler.MCP_PARAMS_DICT:
                    # To avoid repetetive error with postgres mcp "query" tool
                    if step['tool'] == "query":
                        tool_documentation = f"""Tool Name:{step['tool']}\nDescription: {self.dag_compiler.MCP_PARAMS_DICT[step['tool']]['documentation']}\nInput Schema: {self.dag_compiler.MCP_PARAMS_DICT[step['tool']]['parameters']}
                                             The method for this should always be FUNCTION, keep that in mind, and dont do some HTTP Method.
                                             The SQL Database type is Postgres, so please write the SQL Statements Accordingly.
                                          """

                    else:
                        tool_documentation = f"""Tool Name:{step['tool']}\nDescription: {self.dag_compiler.MCP_PARAMS_DICT[step['tool']]['documentation']}\nInput Schema: {self.dag_compiler.MCP_PARAMS_DICT[step['tool']]['parameters']}
                                                The method for this should always be FUNCTION, keep that in mind, and dont do some HTTP Method.
                                            """
                else:
                    raise ValueError("tool Documentation Not Found.")
                input_data = self.prepare_input_for_tool_running_step(step, tool_documentation)
                print("input_data: ",input_data)

                self.chat_history.append({"role": "user", "content": self.agent_request_prompt})
                self.chat_history.append({"role": "user", "content": input_data})

                run_success = False
                agent_request_error_counter = 0
                tool_call_error_counter = 0
                parse_error_bool = False
                tool_call_success_bool = False
                while not run_success and agent_request_error_counter < 5 and tool_call_error_counter < 3:

                    agent_request_error_counter += 1
                    try:
                        agent_request_llm = await self.async_generate()
                        parse_error_bool, parsed_agent_request = self.parse_agent_request(agent_request_llm)
                        print("agent_request_llm: ",agent_request_llm)
                        if parse_error_bool:
                            assistance_request_bool = True
                            assistance_error_dict = parsed_agent_request
                            break
                        run_success = True
                    except Exception as e:
                        error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT and AGENT_REQUEST without any other details before or after.:\n {str(e)}' 
                        self.chat_history.append({"role": "user", "content": error_message})
                        continue

                    tool_call_error_counter += 1
                    run_success=False
                    try:
                        print(parsed_agent_request['agent_requests'])
                        for tool_req_i in range(len(parsed_agent_request['agent_requests'])):
                            if parsed_agent_request['agent_requests'][tool_req_i]['method'] == "FUNCTION":
                                if parsed_agent_request['agent_requests'][tool_req_i]['url'] in self.dag_compiler.MCP_PARAMS_DICT.keys():
                                    print("tool_req_i in self.dag_compiler.MCP_PARAMS_DICT.keys()")
                                    _, mcp_output = await self.dag_compiler.mcp_tool_manager.call_tool(parsed_agent_request['agent_requests'][tool_req_i]['url'],parsed_agent_request['agent_requests'][tool_req_i]['body'])
                                    print(mcp_output)
                                    try:
                                        tool_call_success_bool, tool_output = not(mcp_output.isError), mcp_output
                                    except:
                                        tool_call_success_bool, tool_output = not(mcp_output['error']), mcp_output
                                else:
                                    tool_call_success_bool, tool_output = self.function_call(step['tool'], parsed_agent_request['agent_requests'][tool_req_i]['body'])
                            else:
                                tool_call_success_bool, tool_output = self.requests_func(parsed_agent_request['agent_requests'][tool_req_i]['method'], parsed_agent_request['agent_requests'][tool_req_i]['url'], parsed_agent_request['agent_requests'][tool_req_i]['headers'], parsed_agent_request['agent_requests'][tool_req_i]['body'])

                            print("tool_output : ",tool_output)
                            print("tool_call_success_bool : ",tool_call_success_bool)
                            # if tool_output is too big then we will truncate if required and then summarize here itself else it would take a lot of context
                            # Truncating the tool output to 80000 characters
                            if len(str(tool_output)) > 80000:
                                print("Earlier character length was more than 80000, to be precise it was: ",len(str(tool_output)))
                                tool_output = str(tool_output)[:80000]
                                print("After the length became: ", len(str(tool_output)))
                            print("num of tokens : ",self.num_tokens_from_string(f"{tool_output}"))
                            if self.num_tokens_from_string(f"{tool_output}") > 10000:
                                llm_input_tool_output_summarize = self.prepare_input_for_tool_output_summarize(tool_output, self.sub_task_no, step_no)
                                print("llm_input_tool_output_summarize : ",llm_input_tool_output_summarize)
                                self.chat_history.append({"role": "user", "content": llm_input_tool_output_summarize })
                                llm_output_tool_output_summarize = await self.async_generate()
                                self.chat_history.pop()
                                self.chat_history.pop()
                                tool_output = llm_output_tool_output_summarize
                                print("after summarize num of tokens : ",self.num_tokens_from_string(f"{tool_output}"))


                            if not tool_call_success_bool:
                                assistance_request_bool = True
                                assistance_error_dict = tool_output
                                raise ValueError(f"tool_output : {tool_output}")
                            
                            tool_outputs_list.append(tool_output)

                        run_success = True
                        assistance_request_bool = False
                        assistance_error_dict = None
                    except Exception as e:
                        error_message = f'There was an error while running the tool, please rectify based on this error message, only output the CHAIN_OF_THOUGHT and AGENT_REQUEST without any other details before or after. Carefully review the tool call and its documentation to identify and then rectify it.:\n {str(e)}' 
                        self.chat_history.append({"role": "user", "content": error_message})
                        print("tool running error_message : ",error_message)
                        tool_outputs_list = []

                if assistance_request_bool:
                    break

                if not run_success:
                    raise ValueError("Something is going wrong with the llm or the parsing function or tool calling fucntion. It is not an expected kind of error.")
                    
                #########################################################
                # AGENT RESPONSE Part with Error Handling

                # give the tool_output to LLM and ask it to first verify if it seems plausile for our expectations from the tool, then save the relevant part in the right format
                # additionally the LLM Agent will check if the tool output has enough information such that we can fulfil the input variable requirement for future steps which depend on its output, and retrieve the relevant information and save it in the right format
                tool_output_llm_input = self.prepare_input_for_tool_output(tool_outputs_list, self.sub_task_no, step_no)
                self.chat_history.append({"role": "user", "content": self.agent_response_prompt}) 
                self.chat_history.append({"role": "user", "content": tool_output_llm_input })


                run_success = False
                counter = 0
                while not run_success and counter < 5:
                    counter += 1
                    try:
                        agent_response_llm_output = await self.async_generate()
                        agent_response_parsed_output = self.parse_and_store_agent_response(agent_response_llm_output, self.sub_task_no, step_no)
                        if 'status_code' in agent_response_parsed_output:
                            assistance_request_bool =  True
                            assistance_error_dict = agent_response_parsed_output
                            break

                        print("agent_response_parsed_output : ",agent_response_parsed_output)

                        run_success = True
                    except Exception as e:
                        error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT and AGENT_RESPONSE without any other details before or after.:\n {str(e)}' 
                        self.chat_history.append({"role": "user", "content": error_message})

                if assistance_request_bool:
                    break

            
                if not run_success:
                    raise ValueError("Something is going wrong with the llm or the parsing function in AGENT RESPONSE. It is not an expected kind of error.")
                    
                #########################################################
                # Saving the updated execution_blueprint with tool output values
                with open(f"execution_blueprint_updated_{self.group_id}.json", "w") as json_file:
                    json.dump(self.group_execution_blueprint, json_file, indent=4)

                #########################################################
                # Running STATUS UPDATE part
                status_assist_input = self.prepare_status_assistance_input(self.group_execution_blueprint, step_no)
                print("\nstatus_assist_input : ",status_assist_input)
                
                self.chat_history.append({"role": "user", "content": self.status_assistance_prompt}) 
                self.chat_history.append({"role": "user", "content": status_assist_input}) 

                run_success = False
                counter = 0
                while not run_success and counter < 5:
                    counter += 1
                    try:
                        status_update = await self.async_generate()
                        print("\nstatus_update : ",status_update)
                        parsed_status_update = self.parse_status_assistance_input(status_update)
                        print("\parsed_status_update : ",parsed_status_update)
                        run_success = True
                    except Exception as e:
                        error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT and STATUS_UPDATE without any other details before or after.:\n {str(e)}' 
                        self.chat_history.append({"role": "user", "content": error_message})
                        print("error_message : ",error_message)
                
                if not run_success:
                    raise ValueError("Something is going wrong with the llm or the parsing function in status_update without assistance request. It is not an expected kind of error.")
                
                self.prev_status_update = parsed_status_update['status_update']

            #########################################################
            # ASSISTANCE REQUEST
            if assistance_request_bool:
                status_assist_input = self.prepare_status_assistance_input(self.group_execution_blueprint, step_no, assistance_error_dict)
                print("\nstatus_assist_input : ",status_assist_input)
                self.chat_history.append({"role": "user", "content": self.status_assistance_prompt}) 
                self.chat_history.append({"role": "user", "content": status_assist_input}) 

                run_success = False
                counter = 0
                while not run_success and counter < 5:
                    counter += 1
                    try:
                        status_update = await self.async_generate()
                        print("\nstatus_update : ",status_update)
                        parsed_status_update = self.parse_status_assistance_input(status_update)
                        print("\nparsed_status_update : ",parsed_status_update)
                        run_success = True
                    except Exception as e:
                        error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT, STATUS_UPDATE and ASSISTANCE_REQUEST without any other details before or after.:\n {str(e)}' 
                        self.chat_history.append({"role": "user", "content": error_message})
                        print("error_message : ",error_message)
                
                if not run_success:
                    raise ValueError("Something is going wrong with the llm or the parsing function in status_update with assistance request. It is not an expected kind of error.")

                # Communicating with the DAG Compiler for modificiation of execution blueprint based on the context of the error
                await self.dag_compiler.communicate(parsed_status_update, self.sub_task_no, self)
                print("\nafter self.dag_compiler.communicate(parsed_status_update, self.sub_task_no, self)")
                try:
                    await self.wait_for_response()
                except TimeoutError:
                    print(f"Timeout waiting for response from DAG Compiler for sub_task {self.sub_task_no}")
                    return None
                
                print("after try and timeout")

                # Two possibilites after execution bluepring modification; either the sub_task is dropped or is modified to avoid error
                if self.drop:
                    return None
                if self.modify:
                    return None

                await asyncio.sleep(0.2)
                continue
            else:
                overall_success_bool = True

        if not overall_success_bool:
            raise ValueError(f"Overall the execution_blueprint failed for {self.sub_task_no}")


    def get_results(self):
        # final_execution_blueprint_with_values = self.make_final_execution_blueprint_with_output_values(self.group_execution_blueprint, self.dag_compiler.subtask_list)
        return {
            'sub_task_description' : self.sub_task_description,
            'output' : "Done"
        }

            
    async def run_in_thread(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.build_verify)