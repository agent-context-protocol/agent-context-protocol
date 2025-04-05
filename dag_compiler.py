from base import BaseNode
import re
import json
import asyncio
from available_apis.rapid_apis_format.return_dict import RAPID_APIS_DICT, RAPID_REQD_PARAMS_DICT, RAPID_PARAMS_DICT
from available_apis.function_format.return_dict import FUNCTION_APIS_DOCUMENTATION_DICT, FUNCTION_APIS_REQD_PARAMS_DICT, FUNCTION_APIS_PARAMS_DICT

class DAGCompilerNode(BaseNode):
    def __init__(self, node_name, system_prompt = None):
        super().__init__(node_name, system_prompt)
        self.get_system_prompts()
        self.clusters = {}
        self.lock = asyncio.Lock()
        self.queue = asyncio.Queue()
        self.execution_blueprint = None

        self.unique_apis = {}

    def get_system_prompts(self):
        # execution_blueprint_creation_prompt
        with open('prompts/dag_compiler/execution_blueprint_creation_prompt.txt', 'r') as file:
            self.execution_blueprint_creation_prompt = file.read()

        # execution_blueprint_creation_prompt
        with open('prompts/dag_compiler/status_assistance_prompt.txt', 'r') as file:
            self.status_assistance_prompt = file.read()

    ########################
    # ALL THE PARSING FUNCTIONS WILL BE HERE

    def parse_dag_compiler_execution_blueprint(self, text, restrict_one_group = False, modified_execution_blueprint_bool = False):
        # First, split the text into CHAIN_OF_THOUGHT and execution_blueprint sections
        sections = re.split(r"\$\$execution_blueprint\$\$", text)
        if len(sections) != 2:
            raise ValueError("The text does not contain exactly one CHAIN_OF_THOUGHT and one execution_blueprint section.")

        chain_of_thought_text = sections[0].replace("$$CHAIN_OF_THOUGHT$$", "").strip()
        execution_blueprint_text = sections[1].strip()

        # Extract the CHAIN_OF_THOUGHT
        chain_of_thought = chain_of_thought_text

        # Helper function to skip empty lines
        def skip_empty_lines(lines, index):
            while index < len(lines) and not lines[index].strip():
                index += 1
            return index

        # Now parse the execution_blueprint section
        # Split based on "Group X:" separator
        group_blocks = re.split(r"(Group \d+:)", execution_blueprint_text)
        execution_blueprints = {}

        for i in range(1, len(group_blocks), 2):
            group_header = group_blocks[i]
            group_content = group_blocks[i + 1]

            # Extract group number
            current_group = int(re.search(r'\d+', group_header).group(0))
            execution_blueprints[current_group] = {}

            group_lines = group_content.strip().split('\n')
            panels_in_group = []
            panel_interdependencies_found = False

            j = 0
            while j < len(group_lines):
                # Skip empty lines
                j = skip_empty_lines(group_lines, j)
                if j >= len(group_lines):
                    break

                line = group_lines[j].strip()

                if line.startswith("execution_blueprint for Panel"):
                    # Extract panel ID
                    panel_id = int(re.search(r'\d+', line).group(0))
                    execution_blueprints[current_group][panel_id] = {"panel_description": None, "steps": {}}
                    steps = execution_blueprints[current_group][panel_id]["steps"]
                    panels_in_group.append(panel_id)
                    j += 1

                    # Skip empty lines
                    j = skip_empty_lines(group_lines, j)
                    if j >= len(group_lines):
                        raise ValueError(f"Missing content after 'execution_blueprint for Panel {panel_id}'")

                    # Parse Panel Description
                    if group_lines[j].strip().startswith("Panel Description:"):
                        panel_desc = group_lines[j].split("Panel Description:")[1].strip()
                        execution_blueprints[current_group][panel_id]["panel_description"] = panel_desc
                        j += 1
                    else:
                        raise ValueError(f"Missing Panel Description for Panel {panel_id}")

                    # Skip empty lines
                    j = skip_empty_lines(group_lines, j)
                    if j >= len(group_lines):
                        raise ValueError(f"Missing content after Panel Description for Panel {panel_id}")

                    # Check for 'execution_blueprint Steps:'
                    if group_lines[j].strip() == "execution_blueprint Steps:":
                        j += 1
                    else:
                        raise ValueError(f"Missing 'execution_blueprint Steps:' section for Panel {panel_id}")

                    # Parse Steps
                    while j < len(group_lines):
                        # Skip empty lines
                        j = skip_empty_lines(group_lines, j)
                        if j >= len(group_lines):
                            break

                        line = group_lines[j].strip()
                        if line.startswith("execution_blueprint for Panel") or line.startswith("Group"):
                            break  # Move to the next panel or group

                        # Parse Step
                        if line.startswith("Step"):
                            # Initializing the required parameters for this api
                            reqd_params_for_this_api = None
                            # Extract step number
                            step_counter = int(re.search(r'\d+', line).group(0))
                            current_step = {'api': '', 'handles': '', 'input_vars': [], 'output_vars': []}
                            j += 1

                            # Skip empty lines
                            j = skip_empty_lines(group_lines, j)

                            # Parse Step Details
                            while j < len(group_lines):
                                # Skip empty lines
                                j = skip_empty_lines(group_lines, j)
                                if j >= len(group_lines):
                                    break

                                line = group_lines[j].strip()
                                if line.startswith("Step") or line.startswith("execution_blueprint for Panel") or line.startswith("Group"):
                                    break  # Next step, panel, or group

                                if line.startswith("- API:"):
                                    current_step['api'] = line.split("- API:")[1].strip()
                                    if current_step['api'] in RAPID_REQD_PARAMS_DICT:
                                        reqd_params_for_this_api = list(RAPID_REQD_PARAMS_DICT[current_step['api']].keys())
                                    elif current_step['api'] in FUNCTION_APIS_REQD_PARAMS_DICT:
                                        reqd_params_for_this_api = list(FUNCTION_APIS_REQD_PARAMS_DICT[current_step['api']].keys())
                                    elif current_step['api'] not in RAPID_PARAMS_DICT or current_step['api'] not in FUNCTION_APIS_PARAMS_DICT:
                                        raise ValueError(f"Invalid API Name {current_step['api']}, there is no such API name. Please use a valid api name.")
                                    print(f"current_step['api']: {current_step['api']} reqd_params_for_this_api : {reqd_params_for_this_api}")
                                    j += 1
                                elif line.startswith("- Handles:"):
                                    current_step['handles'] = line.split("- Handles:")[1].strip()
                                    j += 1
                                elif line.startswith("- Input Variables:"):
                                    j += 1
                                    while j < len(group_lines):
                                        # Skip empty lines
                                        j = skip_empty_lines(group_lines, j)
                                        if j >= len(group_lines):
                                            break
                                        line = group_lines[j].strip()
                                        if line.startswith("- Output Variables:") or line.startswith("Step") or line.startswith("execution_blueprint for Panel") or line.startswith("Group"):
                                            break
                                        if line.startswith("- Name:"):
                                            input_var = {}
                                            # Name
                                            input_var['name'] = line.split("Name:")[1].strip()
                                            j += 1

                                            # Parse Parameter
                                            line = group_lines[j].strip()
                                            if line.startswith("- Parameter:"):
                                                input_var['parameter'] = line.split("Parameter:")[1].strip()

                                                # Extract the parameter string after 'Parameter:'
                                                param_str = line.split("Parameter:")[1].strip()
                                                
                                                # Split the parameters by comma and strip whitespace
                                                parameters = [param.strip() for param in param_str.split(",") if param.strip()]

                                                for param_ in parameters:
                                                    if current_step['api'] in RAPID_PARAMS_DICT and param_ not in RAPID_PARAMS_DICT[current_step['api']]:
                                                        raise ValueError(f"Given parameter name {param_} is invalid parameter for API {current_step['api']}, there is no such parameter for this API. The valid parameters for this api are {RAPID_PARAMS_DICT[current_step['api']]}.")
                                                    elif current_step['api'] in FUNCTION_APIS_PARAMS_DICT and param_ not in FUNCTION_APIS_PARAMS_DICT[current_step['api']]:
                                                        raise ValueError(f"Given parameter name {param_} is invalid parameter for API {current_step['api']}, there is no such parameter for this API. Please use a valid parameter for this API {FUNCTION_APIS_PARAMS_DICT[current_step['api']]}.")
                                                    
                                                
                                                # Assign the list of parameters to input_var['parameter']
                                                input_var['parameter'] = parameters
                                                
                                                # Iterate through each parameter and remove it from reqd_params_for_this_api if present
                                                for param in parameters:
                                                    if param in reqd_params_for_this_api:
                                                        reqd_params_for_this_api.remove(param)
                                                    # else:
                                                    #     # Optionally, handle cases where the parameter is not found
                                                    #     print(f"Warning: Parameter '{param}' not found in required parameters for this API.")
                                                
                                                # Move to the next line
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Parameter' for input variable in Panel {panel_id}, Step {step_counter}")

                                            # Parse Type
                                            line = group_lines[j].strip()
                                            if line.startswith("- Type:"):
                                                input_var['type'] = line.split("Type:")[1].strip()
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Type' for input variable in Panel {panel_id}, Step {step_counter}")

                                            # Parse Source
                                            line = group_lines[j].strip()
                                            if line.startswith("- Source:"):
                                                input_var['source'] = line.split("Source:")[1].strip()
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Source' for input variable in Panel {panel_id}, Step {step_counter}")

                                            # Parse Description
                                            line = group_lines[j].strip()
                                            if line.startswith("- Description:"):
                                                input_var['description'] = line.split("Description:")[1].strip()
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Description' for input variable in Panel {panel_id}, Step {step_counter}")

                                            # Parse Value
                                            line = group_lines[j].strip()
                                            if line.startswith("- Value:"):
                                                input_var['value'] = input_var['value'] = line.split("Value:")[1].strip().strip('"')
                                                # Check for the correct value based on Source
                                                if input_var['source'] == "LLM_Generated" and input_var['value'] == "None":
                                                    raise ValueError(f"Value should not be 'None' for LLM_Generated source in Panel {panel_id}, Step {step_counter}")
                                                elif input_var['source'] == "API_Output" and input_var['value'] != "None":
                                                    raise ValueError(f"Value should be 'None' for API_Output source in Panel {panel_id}, Step {step_counter}")
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Value' for input variable in Panel {panel_id}, Step {step_counter}")

                                            # Handle dependencies for API_Output
                                            input_var['dependencies'] = []
                                            if "API_Output" in input_var['source']:
                                                # match = re.search(r"Panel (\d+), Step (\d+)", input_var['source'])
                                                match = re.fullmatch(r"API_Output\s*\(Panel\s+(\d+),\s*Step\s+(\d+)\)", input_var['source'])
                                                if match:
                                                    dependent_panel = int(match.group(1))
                                                    dependent_step = int(match.group(2))
                                                    # checking if panel interdependencie are present and using or to propogate it if it ever becomes true
                                                    panel_interdependencies_found = not(dependent_panel == panel_id) or panel_interdependencies_found
                                                    input_var['dependencies'].append({
                                                        "panel": dependent_panel,
                                                        "step": dependent_step
                                                    })
                                                    # Go to the referenced panel and step in execution_blueprints to update "used_by"
                                                    if dependent_panel in execution_blueprints[current_group]:
                                                        if dependent_step in execution_blueprints[current_group][dependent_panel]["steps"]:
                                                            used_step = execution_blueprints[current_group][dependent_panel]["steps"][dependent_step]
                                                            # Find the relevant output variable in the dependent step
                                                            used_by_check_bool = False
                                                            for output_var in used_step["output_vars"]:
                                                                if output_var["name"] == input_var['name']:
                                                                    if 'used_by' not in output_var:
                                                                        output_var['used_by'] = []
                                                                    output_var["used_by"].append({
                                                                        "panel": panel_id,
                                                                        "step": step_counter
                                                                    })
                                                                    used_by_check_bool = True
                                                            if not used_by_check_bool:
                                                                valid_out_var_name_options = [output_var for output_var in used_step["output_vars"]]
                                                                raise ValueError(f"In Step {dependent_step} Panel {dependent_panel}, dependent input variable ({input_var['name']}) has a different name. If there is dependancy between this and Panel {panel_id}, Step {step_counter}, then they should be same. The valid options for the input variable name for Panel {panel_id}, Step {step_counter} considering the dependency is valid are {valid_out_var_name_options}.")
                                                        else:
                                                            raise ValueError(f"Step {dependent_step} not found in Panel {dependent_panel} for the dependency mentioned in Panel {panel_id}, Step {step_counter}. Please check the dependencies in your execution_blueprint carefully.")
                                                    else:
                                                        if dependent_panel > panel_id:
                                                            raise ValueError(f"Current panel (panel no {panel_id}) is referencing a future Panel (panel no {dependent_panel}). Please order the panels such that a panel is not dependent on a future panel.")
                                                        else:
                                                            raise ValueError(f"Panel {dependent_panel} not found in Group {current_group}. The interdependencies should be between panels of the same group, if this interdependency is valid then please put them in the same group.")
                                                else:
                                                    raise ValueError(f"Invalid source format for dependencies in Panel {panel_id}, Step {step_counter}.")
                                            current_step['input_vars'].append(input_var)
                                        else:
                                            j += 1  # Skip any lines that are not input variables
                                    
                                    if len(reqd_params_for_this_api) != 0:
                                        raise ValueError(f"You have not used some of the required input parameters for api name: {current_step['api']}, like {reqd_params_for_this_api}.")
                                elif line.startswith("- Output Variables:"):
                                    j += 1
                                    while j < len(group_lines):
                                        # Skip empty lines
                                        j = skip_empty_lines(group_lines, j)
                                        if j >= len(group_lines):
                                            break
                                        line = group_lines[j].strip()
                                        if line.startswith("Step") or line.startswith("execution_blueprint for Panel") or line.startswith("Group"):
                                            break
                                        if line.startswith("- Name:"):
                                            output_var = {}
                                            # Name
                                            output_var['name'] = line.split("Name:")[1].strip()
                                            j += 1

                                            # Skip empty lines
                                            j = skip_empty_lines(group_lines, j)
                                            if j >= len(group_lines):
                                                raise ValueError(f"Unexpected end of input while parsing output variable in Panel {panel_id}, Step {step_counter}")

                                            # Description
                                            line = group_lines[j].strip()
                                            if line.startswith("- Description:"):
                                                output_var['description'] = line.split("Description:")[1].strip()
                                                if 'used_by' not in output_var:
                                                    output_var['used_by'] = []
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Description' for output variable in Panel {panel_id}, Step {step_counter}")

                                            current_step['output_vars'].append(output_var)
                                        else:
                                            j += 1  # Skip any lines that are not output variables
                                else:
                                    j += 1  # Skip any unrecognized lines within a step

                            # After parsing the step, add it to the steps dictionary
                            steps[step_counter] = current_step
                        else:
                            j += 1  # Move to the next line if not a step

                else:
                    j += 1  # Skip any lines outside of recognized blocks

            # Check for interdependencies. If we are modifying then we cant update panels in the group, so lets allow if there are no interdependencies but still they are in the same group
            if not(modified_execution_blueprint_bool) and len(panels_in_group) > 1 and not panel_interdependencies_found:
                raise ValueError(f"Not all panels have interdependencies in Group {current_group}. Please put them in different groups if no interdependencies are there.")

        # Return the chain_of_thought and execution_blueprints
        return chain_of_thought, execution_blueprints
    
    def parse_status_assistance_output(self, updated_execution_blueprint):
        # Initialize the result dictionary
        result = {
            'chain_of_thought': '',
            'chosen_action': '',
            'execution_blueprint': None  # This will only be filled if the chosen action is MODIFY
        }

        # Split the input string into sections using regular expressions
        sections = re.split(r'\$\$CHAIN_OF_THOUGHT\$\$|\$\$CHOSEN_ACTION\$\$|\$\$execution_blueprint\$\$', updated_execution_blueprint)

        # Check that at least $$CHAIN_OF_THOUGHT$$ and $$CHOSEN_ACTION$$ exist
        if len(sections) < 3:
            raise ValueError("The output must contain $$CHAIN_OF_THOUGHT$$ and $$CHOSEN_ACTION$$ sections.")

        # Parse the chain of thought section
        result['chain_of_thought'] = sections[1].strip()

        # Parse the chosen action section
        chosen_action_text = sections[2].strip()
        if "MODIFY" in chosen_action_text:
            result['chosen_action'] = 'MODIFY'
        elif "DROP_PANEL" in chosen_action_text:
            result['chosen_action'] = 'DROP_PANEL'
        else:
            raise ValueError("The $$CHOSEN_ACTION$$ section must specify either MODIFY or DROP_PANEL.")

        # If the action is MODIFY, we should also parse the execution_blueprint section
        if result['chosen_action'] == 'MODIFY':
            if len(sections) < 4:
                raise ValueError("The output must contain a $$execution_blueprint$$ section if MODIFY is chosen.")
            execution_blueprint_text = sections[3].strip()

            # Parse the execution_blueprint section by passing it to the existing execution_blueprint parser
            dummy_chain_of_thought = "$$CHAIN_OF_THOUGHT$$\nFiller space"
            full_execution_blueprint_text = f"{dummy_chain_of_thought}\n$$execution_blueprint$$\n{execution_blueprint_text}"

            # Call the existing execution_blueprint parser and save the parsed execution_blueprint
            _, result['execution_blueprint'] = self.parse_dag_compiler_execution_blueprint(full_execution_blueprint_text, modified_execution_blueprint_bool = True)

        return result

    # ALL THE CREATING INPUT FOR LLM FUNCTIONS WILL BE HERE
    
    # create input string
    def create_first_input_data(self,query, panels_list):
        """
        Creates structured input data based on the query, panels, and available APIs.
        Returns both a data structure and a formatted string.
        """
        # Initialize the formatted string
        formatted_string = f"**Query:** \"{query}\"\n\n**Interpreter's Panel Requests:**\n"

        # Initialize a set to keep track of unique APIs
        unique_apis = {}

        # Add the panel descriptions along with the relevant API names
        for panel in panels_list:
            # print("panellllll : ",panel)
            formatted_string += f"{panel['instance_id']}. Panel {panel['instance_id']}: {panel['panel_description']}\n"
            formatted_string += f"Details: {panel['request']['description']}"
            formatted_string += "\nList of Relevant APIs:\n"

            # Only add API names here and collect unique APIs
            for api in panel['request']['relevant_apis']:
                formatted_string += f"   - {api['api_name']}\n"

                # Store the unique APIs in the dictionary
                if api['api_name'] not in unique_apis:
                    unique_apis[api['api_name']] = {
                        # "Input": api.get('Input', 'N/A'),
                        # "Output": api.get('Output', 'N/A'),
                        "Use": api.get('Use', 'N/A')
                    }
            formatted_string += "\n"  # Add a newline after each panel

        self.unique_apis = unique_apis

        # Now add the full details of each unique API at the end
        formatted_string += "**Description of APIs:**\n"
        api_id = 1
        for api_name, api_details in unique_apis.items():
            if api_name in RAPID_APIS_DICT:
                formatted_string += (
                    f"{api_id}. {api_name}\n"
                    f"   - **Use:** {api_details['Use']}\n\n"
                    f"   - **Documentation:** {RAPID_APIS_DICT[api_name]}\n\n"
                    f"   - **Required Parameters (If not specified then error will be raised):** {RAPID_REQD_PARAMS_DICT[api_name]}\n\n"
                )
            elif api_name in FUNCTION_APIS_DOCUMENTATION_DICT:
                formatted_string += (
                    f"{api_id}. {api_name}\n"
                    f"   - **Use:** {api_details['Use']}\n\n"
                    f"   - **Documentation:** {FUNCTION_APIS_DOCUMENTATION_DICT[api_name]}\n\n"
                    f"   - **Required Parameters (If not specified then error will be raised):** {FUNCTION_APIS_REQD_PARAMS_DICT[api_name]}\n\n"
                )
            else:
                raise ValueError(f"Invalid API Name {api_name}. It is not there in RAPID_APIS_DICT or FUNCTION_APIS_FUNCTION_DICT. This error is inside create_first_input_data")
            api_id += 1

        return formatted_string
    
    def make_input_status_update(self, group_execution_blueprint_dict, group_no, status_update_dict):
        result = []

        # # Add the panel descriptions along with the relevant API names
        # for panel_no in list(group_execution_blueprint_dict.keys()):
        #     panel = self.panels_list[panel_no]
        #     # print("panellllll : ",panel)
        #     formatted_string += f"{panel['instance_id']}. Panel {panel['instance_id']}: {panel['panel_description']}\n"
        #     formatted_string += f"Details: {panel['request']['description']}"
        #     formatted_string += "\nList of Relevant APIs:\n"

        # Add Group execution_blueprint header
        result.append(f"Group execution_blueprint:\n")

        result.append(f"\nGroup {group_no}:\n")

        # Process each panel's execution_blueprint
        for panel_no, panel_data in group_execution_blueprint_dict.items():
            result.append(f"execution_blueprint for Panel {panel_no}:\n")
            result.append(f"Panel Description: {panel_data['panel_description']}\n")
            result.append("\nexecution_blueprint Steps:\n")

            # Process each step in the panel
            for step_no, step_data in panel_data['steps'].items():
                result.append(f"Step {step_no}")
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

            result.append("\n")  # Add spacing between execution_blueprints

        # Add Available API Descriptions section
        if hasattr(self, 'unique_apis'):
            result.append("Available API Descriptions:\n")
            api_id = 1
            for api_name, api_details in self.unique_apis.items():
                if api_name in RAPID_APIS_DICT:
                    result.append(f"{api_id}. {api_name}")
                    result.append(f"   - **Use:** {api_details['Use']}\n")
                    result.append(f"   - **Documentation:** {RAPID_APIS_DICT[api_name]}\n")
                    api_id += 1
                elif api_name in FUNCTION_APIS_DOCUMENTATION_DICT:
                    result.append(f"{api_id}. {api_name}")
                    result.append(f"   - **Use:** {api_details['Use']}\n")
                    result.append(f"   - **Documentation:** {FUNCTION_APIS_DOCUMENTATION_DICT[api_name]}\n")
                    api_id += 1
                else:
                    raise ValueError(f"Invalid API Name {api_name}. It is not there in RAPID_APIS_DICT or FUNCTION_APIS_FUNCTION_DICT.")
            result.append("\n")  # Add spacing

        # Add Status Update section
        result.append("Status Update:\n")
        result.append(status_update_dict['status_update'])

        # Add Assistance Request section if present
        result.append("\nAssistance Request:\n")
        result.append(status_update_dict['assistance_request'])

        # Return the final formatted string
        return "\n".join(result)

    ########################
    def setup(self, query, panels_list):
        self.panels_list = panels_list
        # Logic to create execution_blueprint and initialize local translator instances
        # We can use self.chat_history to provide context
        formatted_string = self.create_first_input_data(query, panels_list)
        print("\nformatted_string : \n",formatted_string)

        # generating the execution_blueprint from the LLM
        self.chat_history.append({"role": "user", "content": self.execution_blueprint_creation_prompt}) # system prompt for execution_blueprint_creation
        self.chat_history.append({"role": "user", "content": formatted_string})
        run_success = False
        counter = 0
        while not run_success and counter < 5:
            try:
                llm_response_execution_blueprint = self.generate()
                print("llm_response_execution_blueprint : \n",llm_response_execution_blueprint)
                llm_response_execution_blueprint = llm_response_execution_blueprint.replace("**", "").replace("`", "").replace("#","")
                _, execution_blueprint_dict = self.parse_dag_compiler_execution_blueprint(llm_response_execution_blueprint)
                run_success = True
            except Exception as e:
                error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT and execution_blueprint without any other details before or after. Additionaly inlcude in your CHAIN_OF_THOUGHT about what went wrong in the format and rectify it basded on the given information:\n {str(e)}' 
                self.chat_history.append({"role": "user", "content": error_message})
                print("error_message : ",error_message)
            
            counter += 1
        
        if not run_success:
            raise ValueError("SOmething is wrong with the LLM or the parsing main translator execution_blueprint. An error is not expected here")
            
        # print("\llm_response_execution_blueprint:\n")
        # print(llm_response_execution_blueprint)
        # print("\nexecution_blueprints:\n")
        # print(execution_blueprint_dict)
        # Write to a JSON file
        with open("execution_blueprint.json", "w") as json_file:
            json.dump(execution_blueprint_dict, json_file, indent=4)
        # For now, we're loading the execution_blueprint from a file
        with open("execution_blueprint.json", "r") as json_file:
            execution_blueprint_dict = json.load(json_file)
        self.execution_blueprint = execution_blueprint_dict
        return execution_blueprint_dict


    async def communicate(self, update, local_translator_id, local_translator_object):
        await self.queue.put((update, local_translator_id, local_translator_object))
        
    async def process_queue(self):
        while True:
            # Get the next item from the queue without holding the lock
            status_update_dict, local_translator_id, local_translator_object = await self.queue.get()
            print("status_update_dict:", status_update_dict)
            
            # Process the update here
            print(f"Processing update from Local Translator {local_translator_id}")

            # Prepare the input for the LLM
            status_assistance_llm_input = self.make_input_status_update(
                self.execution_blueprint[str(local_translator_object.group_id)], 
                local_translator_object.group_id, 
                status_update_dict
            )

            print("status_assistance_llm_input:", status_assistance_llm_input)

            # Generate the execution_blueprint from the LLM
            self.chat_history.append({"role": "user", "content": self.status_assistance_prompt})  # System prompt for execution_blueprint creation
            self.chat_history.append({"role": "user", "content": status_assistance_llm_input})

            run_success = False
            counter = 0
            while not run_success and counter < 5:
                counter += 1
                try:
                    # If self.generate() is blocking, run it in a separate thread
                    updated_execution_blueprint = await asyncio.to_thread(self.generate)
                    print("updated_execution_blueprint:", updated_execution_blueprint)
                    updated_execution_blueprint = updated_execution_blueprint.replace("**", "").replace("`", "").replace("#","")
                    parsed_updated_execution_blueprint = self.parse_status_assistance_output(updated_execution_blueprint)
                    run_success = True
                except Exception as e:
                    error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT, CHOSEN_ACTION and/or execution_blueprint without any other details before or after. Additionaly inlcude in your CHAIN_OF_THOUGHT about what went wrong in the format and rectify it basded on the given information:\n {str(e)}' 
                    self.chat_history.append({"role": "user", "content": error_message})
                    print("error_message:", error_message)

            if not run_success:
                raise ValueError(
                    "Something is wrong with the LLM or the parsing status_assistance in main translator. "
                    "An error is not expected here."
                )
            
            print("parsed_updated_execution_blueprint['chosen_action']:", parsed_updated_execution_blueprint['chosen_action'])

            if parsed_updated_execution_blueprint['chosen_action'] == "DROP_PANEL":
                # Acquire the lock only when modifying shared resources
                async with self.lock:

                    local_translator_object.drop = True
                print('Sent Request to Drop Panel')

            elif parsed_updated_execution_blueprint['chosen_action'] == "MODIFY":
                # Perform file I/O in a separate thread to avoid blocking the event loop
                updated_execution_blueprint_dict = await asyncio.to_thread(
                    self.save_and_load_execution_blueprint, 
                    local_translator_object.group_id, 
                    parsed_updated_execution_blueprint['execution_blueprint']
                )
                print("updated_execution_blueprint_dict after loading:", updated_execution_blueprint_dict)
                # Acquire the lock when updating shared resources
                async with self.lock:
                    local_translator_object.group_execution_blueprint = updated_execution_blueprint_dict
                    local_translator_object.modify = True
                print('Sent Request to Modify Panel')

            else:
                print("In the else statement")
                raise ValueError("The chosen_action key must specify either MODIFY or DROP_PANEL.")
            
            print(f"Finished processing update from Local Translator {local_translator_id}")
            
            # Yield control to other tasks
            await asyncio.sleep(0.1)  # Use sleep(0) to yield control without delay

    def save_and_load_execution_blueprint(self, group_id, execution_blueprint):
        # Save the execution_blueprint to a file
        filename = f"updated_execution_blueprint_group_{group_id}.json"
        with open(filename, "w") as json_file:
            json.dump(execution_blueprint, json_file, indent=4)
        # Load the execution_blueprint back from the file
        with open(filename, "r") as json_file:
            updated_execution_blueprint_dict = json.load(json_file)
        self.execution_blueprint[str(group_id)] = updated_execution_blueprint_dict
        return updated_execution_blueprint_dict