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

        self.unique_tools = {}

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
            raise ValueError("The text does not contain exactly one CHAIN_OF_THOUGHT and one EXECUTION_BLUEPRINT section.")

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
            subtasks_in_group = []
            subtasks_interdependencies_found = False

            j = 0
            while j < len(group_lines):
                # Skip empty lines
                j = skip_empty_lines(group_lines, j)
                if j >= len(group_lines):
                    break

                line = group_lines[j].strip()

                if line.startswith("execution_blueprint for sub_task"):
                    # Extract sub_task ID
                    subtasks_id = int(re.search(r'\d+', line).group(0))
                    execution_blueprints[current_group][subtasks_id] = {"subtask_description": None, "steps": {}}
                    steps = execution_blueprints[current_group][subtasks_id]["steps"]
                    subtasks_in_group.append(subtasks_id)
                    j += 1

                    # Skip empty lines
                    j = skip_empty_lines(group_lines, j)
                    if j >= len(group_lines):
                        raise ValueError(f"Missing content after execution_blueprint for sub_task {subtasks_id}'")

                    # Parse sub_task Description
                    if group_lines[j].strip().startswith("sub_task Description:"):
                        subtasks_desc = group_lines[j].split("sub_task Description:")[1].strip()
                        execution_blueprints[current_group][subtasks_id]["subtask_description"] = subtasks_desc
                        j += 1
                    else:
                        raise ValueError(f"Missing sub_task Description for sub_task {subtasks_id}")

                    # Skip empty lines
                    j = skip_empty_lines(group_lines, j)
                    if j >= len(group_lines):
                        raise ValueError(f"Missing content after sub_task Description for sub_task {subtasks_id}")

                    # Check for 'execution_blueprint Steps:'
                    if group_lines[j].strip() == "execution_blueprint Steps:":
                        j += 1
                    else:
                        raise ValueError(f"Missing execution_blueprint Steps: section for sub_task {subtasks_id}")

                    # Parse Steps
                    while j < len(group_lines):
                        # Skip empty lines
                        j = skip_empty_lines(group_lines, j)
                        if j >= len(group_lines):
                            break

                        line = group_lines[j].strip()
                        if line.startswith("execution_blueprint for sub_task") or line.startswith("Group"):
                            break  # Move to the next subtask or group

                        # Parse Step
                        if line.startswith("Step"):
                            # Initializing the required parameters for this tool
                            reqd_params_for_this_tool = None
                            # Extract step number
                            step_counter = int(re.search(r'\d+', line).group(0))
                            current_step = {'tool': '', 'handles': '', 'input_vars': [], 'output_vars': []}
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
                                if line.startswith("Step") or line.startswith("execution_blueprint for sub_task") or line.startswith("Group"):
                                    break  # Next step, subtask, or group

                                if line.startswith("- TOOL:"):
                                    current_step['tool'] = line.split("- TOOL:")[1].strip()
                                    if current_step['tool'] in RAPID_REQD_PARAMS_DICT:
                                        reqd_params_for_this_tool = list(RAPID_REQD_PARAMS_DICT[current_step['tool']].keys())
                                    elif current_step['tool'] in FUNCTION_APIS_REQD_PARAMS_DICT:
                                        reqd_params_for_this_tool = list(FUNCTION_APIS_REQD_PARAMS_DICT[current_step['tool']].keys())
                                    elif current_step['tool'] not in RAPID_PARAMS_DICT or current_step['tool'] not in FUNCTION_APIS_PARAMS_DICT:
                                        raise ValueError(f"Invalid TOOL Name {current_step['tool']}, there is no such TOOL name. Please use a valid TOOL name.")
                                    print(f"current_step['tool']: {current_step['tool']} reqd_params_for_this_tool : {reqd_params_for_this_tool}")
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
                                        if line.startswith("- Output Variables:") or line.startswith("Step") or line.startswith("execution_blueprint for sub_task") or line.startswith("Group"):
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
                                                    if current_step['tool'] in RAPID_PARAMS_DICT and param_ not in RAPID_PARAMS_DICT[current_step['tool']]:
                                                        raise ValueError(f"Given parameter name {param_} is invalid parameter for TOOL {current_step['tool']}, there is no such parameter for this TOOL. The valid parameters for this tool are {RAPID_PARAMS_DICT[current_step['tool']]}.")
                                                    elif current_step['tool'] in FUNCTION_APIS_PARAMS_DICT and param_ not in FUNCTION_APIS_PARAMS_DICT[current_step['tool']]:
                                                        raise ValueError(f"Given parameter name {param_} is invalid parameter for TOOL {current_step['tool']}, there is no such parameter for this TOOL. Please use a valid parameter for this TOOL {FUNCTION_APIS_PARAMS_DICT[current_step['tool']]}.")
                                                    
                                                
                                                # Assign the list of parameters to input_var['parameter']
                                                input_var['parameter'] = parameters
                                                
                                                # Iterate through each parameter and remove it from reqd_params_for_this_tool if present
                                                for param in parameters:
                                                    if param in reqd_params_for_this_tool:
                                                        reqd_params_for_this_tool.remove(param)
                                                    # else:
                                                    #     # Optionally, handle cases where the parameter is not found
                                                    #     print(f"Warning: Parameter '{param}' not found in required parameters for this TOOL.")
                                                
                                                # Move to the next line
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Parameter' for input variable in sub_task {subtasks_id}, Step {step_counter}")

                                            # Parse Type
                                            line = group_lines[j].strip()
                                            if line.startswith("- Type:"):
                                                input_var['type'] = line.split("Type:")[1].strip()
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Type' for input variable in sub_task {subtasks_id}, Step {step_counter}")

                                            # Parse Source
                                            line = group_lines[j].strip()
                                            if line.startswith("- Source:"):
                                                input_var['source'] = line.split("Source:")[1].strip()
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Source' for input variable in sub_task {subtasks_id}, Step {step_counter}")

                                            # Parse Description
                                            line = group_lines[j].strip()
                                            if line.startswith("- Description:"):
                                                input_var['description'] = line.split("Description:")[1].strip()
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Description' for input variable in sub_task {subtasks_id}, Step {step_counter}")

                                            # Parse Value
                                            line = group_lines[j].strip()
                                            if line.startswith("- Value:"):
                                                input_var['value'] = input_var['value'] = line.split("Value:")[1].strip().strip('"')
                                                # Check for the correct value based on Source
                                                if input_var['source'] == "LLM_Generated" and input_var['value'] == "None":
                                                    raise ValueError(f"Value should not be 'None' for LLM_Generated source in sub_task {subtasks_id}, Step {step_counter}")
                                                elif input_var['source'] == "TOOL_Output" and input_var['value'] != "None":
                                                    raise ValueError(f"Value should be 'None' for TOOL_Output source in sub_task {subtasks_id}, Step {step_counter}")
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Value' for input variable in sub_task {subtasks_id}, Step {step_counter}")

                                            # Handle dependencies for TOOL_Output
                                            input_var['dependencies'] = []
                                            if "TOOL_Output" in input_var['source']:
                                                # match = re.search(r"sub_task (\d+), Step (\d+)", input_var['source'])
                                                match = re.fullmatch(r"TOOL_Output\s*\(sub_task\s+(\d+),\s*Step\s+(\d+)\)", input_var['source'])
                                                if match:
                                                    dependent_subtask = int(match.group(1))
                                                    dependent_step = int(match.group(2))
                                                    # checking if subtask interdependencie are present and using or to propogate it if it ever becomes true
                                                    subtasks_interdependencies_found = not(dependent_subtask == subtasks_id) or subtasks_interdependencies_found
                                                    input_var['dependencies'].append({
                                                        "sub_task": dependent_subtask,
                                                        "step": dependent_step
                                                    })
                                                    # Go to the referenced subtask and step in execution_blueprints to update "used_by"
                                                    if dependent_subtask in execution_blueprints[current_group]:
                                                        if dependent_step in execution_blueprints[current_group][dependent_subtask]["steps"]:
                                                            used_step = execution_blueprints[current_group][dependent_subtask]["steps"][dependent_step]
                                                            # Find the relevant output variable in the dependent step
                                                            used_by_check_bool = False
                                                            for output_var in used_step["output_vars"]:
                                                                if output_var["name"] == input_var['name']:
                                                                    if 'used_by' not in output_var:
                                                                        output_var['used_by'] = []
                                                                    output_var["used_by"].append({
                                                                        "sub_task": subtasks_id,
                                                                        "step": step_counter
                                                                    })
                                                                    used_by_check_bool = True
                                                            if not used_by_check_bool:
                                                                valid_out_var_name_options = [output_var for output_var in used_step["output_vars"]]
                                                                raise ValueError(f"In Step {dependent_step} sub_task {dependent_subtask}, dependent input variable ({input_var['name']}) has a different name. If there is dependancy between this and sub_task {subtasks_id}, Step {step_counter}, then they should be same. The valid options for the input variable name for sub_task {subtasks_id}, Step {step_counter} considering the dependency is valid are {valid_out_var_name_options}.")
                                                        else:
                                                            raise ValueError(f"Step {dependent_step} not found in sub_task {dependent_subtask} for the dependency mentioned in sub_task {subtasks_id}, Step {step_counter}. Please check the dependencies in your execution_blueprint carefully.")
                                                    else:
                                                        if dependent_subtask > subtasks_id:
                                                            raise ValueError(f"Current sub_task (sub_task no {subtasks_id}) is referencing a future sub_task (sub_task no {dependent_subtask}). Please order the sub_tasks such that a sub_task is not dependent on a future sub_task.")
                                                        else:
                                                            raise ValueError(f"sub_task {dependent_subtask} not found in Group {current_group}. The interdependencies should be between sub_tasks of the same group, if this interdependency is valid then please put them in the same group.")
                                                else:
                                                    raise ValueError(f"Invalid source format for dependencies in sub_task {subtasks_id}, Step {step_counter}.")
                                            current_step['input_vars'].append(input_var)
                                        else:
                                            j += 1  # Skip any lines that are not input variables
                                    
                                    if len(reqd_params_for_this_tool) != 0:
                                        raise ValueError(f"You have not used some of the required input parameters for tool name: {current_step['tool']}, like {reqd_params_for_this_tool}.")
                                elif line.startswith("- Output Variables:"):
                                    j += 1
                                    while j < len(group_lines):
                                        # Skip empty lines
                                        j = skip_empty_lines(group_lines, j)
                                        if j >= len(group_lines):
                                            break
                                        line = group_lines[j].strip()
                                        if line.startswith("Step") or line.startswith("execution_blueprint for sub_task") or line.startswith("Group"):
                                            break
                                        if line.startswith("- Name:"):
                                            output_var = {}
                                            # Name
                                            output_var['name'] = line.split("Name:")[1].strip()
                                            j += 1

                                            # Skip empty lines
                                            j = skip_empty_lines(group_lines, j)
                                            if j >= len(group_lines):
                                                raise ValueError(f"Unexpected end of input while parsing output variable in sub_task {subtasks_id}, Step {step_counter}")

                                            # Description
                                            line = group_lines[j].strip()
                                            if line.startswith("- Description:"):
                                                output_var['description'] = line.split("Description:")[1].strip()
                                                if 'used_by' not in output_var:
                                                    output_var['used_by'] = []
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Description' for output variable in sub_task {subtasks_id}, Step {step_counter}")

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

            # Check for interdependencies. If we are modifying then we cant update sub_task in the group, so lets allow if there are no interdependencies but still they are in the same group
            if not(modified_execution_blueprint_bool) and len(subtasks_in_group) > 1 and not subtasks_interdependencies_found:
                raise ValueError(f"Not all sub_tasks have interdependencies in Group {current_group}. Please put them in different groups if no interdependencies are there.")

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
        elif "DROP_SUBTASK" in chosen_action_text:
            result['chosen_action'] = 'DROP_SUBTASK'
        else:
            raise ValueError("The $$CHOSEN_ACTION$$ section must specify either MODIFY or DROP_SUBTASK.")

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
    def create_first_input_data(self,query, subtask_list):
        """
        Creates structured input data based on the query, subtask, and available Tools.
        Returns both a data structure and a formatted string.
        """
        # Initialize the formatted string
        formatted_string = f"**Query:** \"{query}\"\n\n**TaskDecomposers's sub_task Requests:**\n"

        # Initialize a set to keep track of unique Tools
        unique_tools = {}

        # Add the subtask descriptions along with the relevant Tool names
        for subtask in subtask_list:
            formatted_string += f"{subtask['instance_id']}. sub_task {subtask['instance_id']}: {subtask['subtask_description']}\n"
            formatted_string += f"Details: {subtask['request']['description']}"
            formatted_string += "\nList of Relevant TOOls:\n"

            # Only add Tool names here and collect unique Tools
            for tool in subtask['request']['relevant_tools']:
                formatted_string += f"   - {tool['tool_name']}\n"

                # Store the unique Tools in the dictionary
                if tool['tool_name'] not in unique_tools:
                    unique_tools[tool['tool_name']] = {
                        # "Input": tool.get('Input', 'N/A'),
                        # "Output": tool.get('Output', 'N/A'),
                        "Use": tool.get('Use', 'N/A')
                    }
            formatted_string += "\n"  # Add a newline after each subtask

        self.unique_tools = unique_tools

        # Now add the full details of each unique Tools at the end
        formatted_string += "**Description of Tools:**\n"
        tool_id = 1
        for tool_name, tool_details in unique_tools.items():
            if tool_name in RAPID_APIS_DICT:
                formatted_string += (
                    f"{tool_id}. {tool_name}\n"
                    f"   - **Use:** {tool_details['Use']}\n\n"
                    f"   - **Documentation:** {RAPID_APIS_DICT[tool_name]}\n\n"
                    f"   - **Required Parameters (If not specified then error will be raised):** {RAPID_REQD_PARAMS_DICT[tool_name]}\n\n"
                )
            elif tool_name in FUNCTION_APIS_DOCUMENTATION_DICT:
                formatted_string += (
                    f"{tool_id}. {tool_name}\n"
                    f"   - **Use:** {tool_details['Use']}\n\n"
                    f"   - **Documentation:** {FUNCTION_APIS_DOCUMENTATION_DICT[tool_name]}\n\n"
                    f"   - **Required Parameters (If not specified then error will be raised):** {FUNCTION_APIS_REQD_PARAMS_DICT[tool_name]}\n\n"
                )
            else:
                raise ValueError(f"Invalid TOOL Name {tool_name}. It is not there in RAPID_APIS_DICT or FUNCTION_APIS_FUNCTION_DICT. This error is inside create_first_input_data")
            tool_id += 1

        return formatted_string
    
    def make_input_status_update(self, group_execution_blueprint_dict, group_no, status_update_dict):
        result = []

        # Add Group execution_blueprint header
        result.append(f"Group execution_blueprint:\n")

        result.append(f"\nGroup {group_no}:\n")

        # Process each sub_task's execution_blueprint
        for subtask_no, subtask_data in group_execution_blueprint_dict.items():
            result.append(f"execution_blueprint for sub_task {subtask_no}:\n")
            result.append(f"sub_task Description: {subtask_data['subtask_description']}\n")
            result.append("\nexecution_blueprint Steps:\n")

            # Process each step in the sub_task
            for step_no, step_data in subtask_data['steps'].items():
                result.append(f"Step {step_no}")
                result.append(f"- TOOL: {step_data['tool']}")
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

        # Add Available TOOL Descriptions section
        if hasattr(self, 'unique_tools'):
            result.append("Available TOOL Descriptions:\n")
            tool_id = 1
            for tool_name, tool_details in self.unique_tools.items():
                if tool_name in RAPID_APIS_DICT:
                    result.append(f"{tool_id}. {tool_name}")
                    result.append(f"   - **Use:** {tool_details['Use']}\n")
                    result.append(f"   - **Documentation:** {RAPID_APIS_DICT[tool_name]}\n")
                    tool_id += 1
                elif tool_name in FUNCTION_APIS_DOCUMENTATION_DICT:
                    result.append(f"{tool_id}. {tool_name}")
                    result.append(f"   - **Use:** {tool_details['Use']}\n")
                    result.append(f"   - **Documentation:** {FUNCTION_APIS_DOCUMENTATION_DICT[tool_name]}\n")
                    tool_id += 1
                else:
                    raise ValueError(f"Invalid TOOL Name {tool_name}. It is not there in RAPID_APIS_DICT or FUNCTION_APIS_FUNCTION_DICT.")
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
    def setup(self, query, subtask_list):
        self.subtask_list = subtask_list
        # Logic to create execution_blueprint and initialize agent instances
        # We can use self.chat_history to provide context
        formatted_string = self.create_first_input_data(query, subtask_list)
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
                error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT and EXECUTION_BLUEPRINT without any other details before or after. Additionaly inlcude in your CHAIN_OF_THOUGHT about what went wrong in the format and rectify it basded on the given information:\n {str(e)}' 
                self.chat_history.append({"role": "user", "content": error_message})
                print("error_message : ",error_message)
            
            counter += 1
        
        if not run_success:
            raise ValueError("SOmething is wrong with the LLM or the parsing dag compiler execution_blueprint. An error is not expected here")
            

        # Write to a JSON file
        with open("execution_blueprint.json", "w") as json_file:
            json.dump(execution_blueprint_dict, json_file, indent=4)
        # For now, we're loading the execution_blueprint from a file
        with open("execution_blueprint.json", "r") as json_file:
            execution_blueprint_dict = json.load(json_file)
        self.execution_blueprint = execution_blueprint_dict
        return execution_blueprint_dict


    async def communicate(self, update, agent_id, agent_object):
        await self.queue.put((update, agent_id, agent_object))
        
    async def process_queue(self):
        while True:
            # Get the next item from the queue without holding the lock
            status_update_dict, agent_id, agent_object = await self.queue.get()
            print("status_update_dict:", status_update_dict)
            
            # Process the update here
            print(f"Processing update from Agent {agent_id}")

            # Prepare the input for the LLM
            status_assistance_llm_input = self.make_input_status_update(
                self.execution_blueprint[str(agent_object.group_id)], 
                agent_object.group_id, 
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
                    error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT, CHOSEN_ACTION and/or EXECUTION_BLUEPRINT without any other details before or after. Additionaly inlcude in your CHAIN_OF_THOUGHT about what went wrong in the format and rectify it basded on the given information:\n {str(e)}' 
                    self.chat_history.append({"role": "user", "content": error_message})
                    print("error_message:", error_message)

            if not run_success:
                raise ValueError(
                    "Something is wrong with the LLM or the parsing status_assistance in dag compiler process_queue. "
                    "An error is not expected here."
                )
            
            print("parsed_updated_execution_blueprint['chosen_action']:", parsed_updated_execution_blueprint['chosen_action'])

            if parsed_updated_execution_blueprint['chosen_action'] == "DROP_SUBTASK":
                # Acquire the lock only when modifying shared resources
                async with self.lock:

                    agent_object.drop = True
                print('Sent Request to Drop sub_task')

            elif parsed_updated_execution_blueprint['chosen_action'] == "MODIFY":
                # Perform file I/O in a separate thread to avoid blocking the event loop
                updated_execution_blueprint_dict = await asyncio.to_thread(
                    self.save_and_load_execution_blueprint, 
                    agent_object.group_id, 
                    parsed_updated_execution_blueprint['execution_blueprint']
                )
                print("updated_execution_blueprint_dict after loading:", updated_execution_blueprint_dict)
                # Acquire the lock when updating shared resources
                async with self.lock:
                    agent_object.group_execution_blueprint = updated_execution_blueprint_dict
                    agent_object.modify = True
                print('Sent Request to Modify sub_task')

            else:
                print("In the else statement")
                raise ValueError("The chosen_action key must specify either MODIFY or DROP_SUBTASK.")
            
            print(f"Finished processing update from Agent {agent_id}")
            
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