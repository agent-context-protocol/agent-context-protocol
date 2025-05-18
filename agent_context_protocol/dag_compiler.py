from .base import BaseNode
import re
import json
import traceback 
import asyncio
from .available_tools.rapid_apis_format.return_dict import RAPIDAPI_TOOLS_DICT, RAPIDAPI_REQD_PARAMS_DICT, RAPIDAPI_PARAMS_DICT
from .available_tools.function_format.return_dict import FUNCTION_TOOLS_DOCUMENTATION_DICT, FUNCTION_TOOLS_REQD_PARAMS_DICT, FUNCTION_TOOLS_PARAMS_DICT
from importlib import resources
import agent_context_protocol.prompts.dag_compiler as dag_compiler_prompts
class DAGCompilerNode(BaseNode):
    def __init__(self, node_name, system_prompt = None, mcp_tool_manager = None):
        super().__init__(node_name, system_prompt)
        self.get_system_prompts()
        self.clusters = {}
        self.lock = asyncio.Lock()
        self.queue = asyncio.Queue()
        self.execution_blueprint = None
        self.mcp_tool_manager = mcp_tool_manager
        self.unique_tools = {}
        self.MCP_PARAMS_DICT = self.mcp_tool_manager.return_documentation()

    def get_system_prompts(self):
        with resources.open_text(dag_compiler_prompts, "execution_blueprint_creation_prompt.txt") as file:
            self.execution_blueprint_creation_prompt = file.read()

        with resources.open_text(dag_compiler_prompts, "status_assistance_prompt.txt") as file:
            self.status_assistance_prompt = file.read()

    ########################
    # ALL THE PARSING FUNCTIONS WILL BE HERE

    def parse_dag_compiler_execution_blueprint(self, text, restrict_one_group = False, modified_execution_blueprint_bool = False):
        sections = re.split(r"\$\$EXECUTION_BLUEPRINT\$\$", text)
        if len(sections) != 2:
            raise ValueError("The text does not contain exactly one CHAIN_OF_THOUGHT and one EXECUTION_BLUEPRINT section.")

        chain_of_thought_text = sections[0].replace("$$CHAIN_OF_THOUGHT$$", "").strip()
        execution_blueprint_text = sections[1].strip()

        chain_of_thought = chain_of_thought_text

        def skip_empty_lines(lines, index):
            while index < len(lines) and not lines[index].strip():
                index += 1
            return index

        group_blocks = re.split(r"(Group \d+:)", execution_blueprint_text)
        execution_blueprints = {}

        output_variables_name = []

        for i in range(1, len(group_blocks), 2):
            group_header = group_blocks[i]
            group_content = group_blocks[i + 1]

            current_group = int(re.search(r'\d+', group_header).group(0))
            execution_blueprints[current_group] = {}

            group_lines = group_content.strip().split('\n')
            subtasks_in_group = []
            subtasks_interdependencies_found = False

            j = 0
            while j < len(group_lines):
                j = skip_empty_lines(group_lines, j)
                if j >= len(group_lines):
                    break

                line = group_lines[j].strip()

                if line.startswith("execution_blueprint for sub_task"):
                    subtasks_id = int(re.search(r'\d+', line).group(0))
                    execution_blueprints[current_group][subtasks_id] = {"subtask_description": None, "steps": {}}
                    steps = execution_blueprints[current_group][subtasks_id]["steps"]
                    subtasks_in_group.append(subtasks_id)
                    j += 1

                    j = skip_empty_lines(group_lines, j)
                    if j >= len(group_lines):
                        raise ValueError(f"Missing content after execution_blueprint for sub_task {subtasks_id}'")

                    if group_lines[j].strip().startswith("sub_task Description:"):
                        subtasks_desc = group_lines[j].split("sub_task Description:")[1].strip()
                        execution_blueprints[current_group][subtasks_id]["subtask_description"] = subtasks_desc
                        j += 1
                    else:
                        raise ValueError(f"Missing sub_task Description for sub_task {subtasks_id}")

                    j = skip_empty_lines(group_lines, j)
                    if j >= len(group_lines):
                        raise ValueError(f"Missing content after sub_task Description for sub_task {subtasks_id}")

                    if group_lines[j].strip() == "execution_blueprint Steps:":
                        j += 1
                    else:
                        raise ValueError(f"Missing execution_blueprint Steps: section for sub_task {subtasks_id}")

                    step_input_variables = []
                    while j < len(group_lines):
                        j = skip_empty_lines(group_lines, j)
                        if j >= len(group_lines):
                            break

                        line = group_lines[j].strip()
                        if line.startswith("execution_blueprint for sub_task") or line.startswith("Group"):
                            break 

                        if line.startswith("Step"):
                            reqd_params_for_this_tool = None
                            step_counter_match = re.search(r'(?<!\d\.)\b\d+\b(?!\.\d)', line)
                            if not step_counter_match:
                                raise ValueError("Step numbers should be defined as Step step_no and not Step sub_task_no.step_no")
                            step_counter = int(step_counter_match.group(0)) #int(re.search(r'\d+', line).group(0))
                            current_step = {'tool': '', 'handles': '', 'input_vars': [], 'output_vars': []}
                            j += 1

                            j = skip_empty_lines(group_lines, j)

                            while j < len(group_lines):
                                j = skip_empty_lines(group_lines, j)
                                if j >= len(group_lines):
                                    break

                                line = group_lines[j].strip()
                                if line.startswith("Step") or line.startswith("execution_blueprint for sub_task") or line.startswith("Group"):
                                    break  

                                if line.startswith("- TOOL:"):
                                    current_step['tool'] = line.split("- TOOL:")[1].strip()
                                    if current_step['tool'] in RAPIDAPI_REQD_PARAMS_DICT:
                                        reqd_params_for_this_tool = list(RAPIDAPI_REQD_PARAMS_DICT[current_step['tool']].keys())
                                    elif current_step['tool'] in FUNCTION_TOOLS_REQD_PARAMS_DICT:
                                        reqd_params_for_this_tool = list(FUNCTION_TOOLS_REQD_PARAMS_DICT[current_step['tool']].keys())
                                    elif current_step['tool'] in self.MCP_PARAMS_DICT.keys():
                                        try:
                                            reqd_params_for_this_tool = self.MCP_PARAMS_DICT[current_step['tool']]['parameters_dict'].get('required', '')
                                        except:
                                            reqd_params_for_this_tool = []
                                    elif current_step['tool'] not in RAPIDAPI_PARAMS_DICT or current_step['tool'] not in FUNCTION_TOOLS_PARAMS_DICT or current_step['tool'] not in self.MCP_PARAMS_DICT.keys():
                                        raise ValueError(f"Invalid TOOL Name {current_step['tool']}, there is no such TOOL name. Please use a valid TOOL name.")
                                    print(f"current_step['tool']: {current_step['tool']} reqd_params_for_this_tool : {reqd_params_for_this_tool}")
                                    j += 1
                                elif line.startswith("- Handles:"):
                                    current_step['handles'] = line.split("- Handles:")[1].strip()
                                    j += 1
                                elif line.startswith("- Input Variables:"):
                                    j += 1
                                    while j < len(group_lines):
                                        j = skip_empty_lines(group_lines, j)
                                        if j >= len(group_lines):
                                            break
                                        line = group_lines[j].strip()
                                        if line.startswith("- Output Variables:") or line.startswith("Step") or line.startswith("execution_blueprint for sub_task") or line.startswith("Group"):
                                            break
                                        if line.startswith("- Name:"):
                                            input_var = {}
                                            input_var['name'] = line.split("Name:")[1].strip()
                                            step_input_variables.append(input_var['name'])
                                            j += 1

                                            line = group_lines[j].strip()
                                            if line.startswith("- Parameter:"):
                                                input_var['parameter'] = line.split("Parameter:")[1].strip()

                                                param_str = line.split("Parameter:")[1].strip()
                                                
                                                parameters = [param.strip() for param in param_str.split(",") if param.strip()]

                                                for param_ in parameters:
                                                    if current_step['tool'] in RAPIDAPI_PARAMS_DICT and param_ not in RAPIDAPI_PARAMS_DICT[current_step['tool']]:
                                                        raise ValueError(f"Given parameter name {param_} is invalid parameter for TOOL {current_step['tool']}, there is no such parameter for this TOOL. The valid parameters for this tool are {RAPIDAPI_PARAMS_DICT[current_step['tool']]}.")
                                                    elif current_step['tool'] in FUNCTION_TOOLS_PARAMS_DICT and param_ not in FUNCTION_TOOLS_PARAMS_DICT[current_step['tool']]:
                                                        raise ValueError(f"Given parameter name {param_} is invalid parameter for TOOL {current_step['tool']}, there is no such parameter for this TOOL. Please use a valid parameter for this TOOL {FUNCTION_TOOLS_PARAMS_DICT[current_step['tool']]}.")
                                                    
                                                
                                                input_var['parameter'] = parameters
                                                
                                                for param in parameters:
                                                    if param in reqd_params_for_this_tool:
                                                        reqd_params_for_this_tool.remove(param)

                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Parameter' for input variable in sub_task {subtasks_id}, Step {step_counter}")

                                            line = group_lines[j].strip()
                                            if line.startswith("- Type:"):
                                                input_var['type'] = line.split("Type:")[1].strip()
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Type' for input variable in sub_task {subtasks_id}, Step {step_counter}")

                                            line = group_lines[j].strip()
                                            if line.startswith("- Source:"):
                                                input_var['source'] = line.split("Source:")[1].strip()
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Source' for input variable in sub_task {subtasks_id}, Step {step_counter}")

                                            line = group_lines[j].strip()
                                            if line.startswith("- Description:"):
                                                input_var['description'] = line.split("Description:")[1].strip()
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Description' for input variable in sub_task {subtasks_id}, Step {step_counter}")

                                            line = group_lines[j].strip()
                                            if line.startswith("- Value:"):
                                                input_var['value'] = input_var['value'] = line.split("Value:")[1].strip().strip('"')
                                                if "TOOL_Output" in input_var['value'] or "sub_task" in input_var['value']:
                                                    raise ValueError(f"Value should not refer to previous steps output variable names or TOOL_Output or sub_tasks directly, if the purpose is to derive the parameters input variable value from a previous steps output variable then parameter source field should be TOOL_Output with value as None in sub_task {subtasks_id}, Step {step_counter}")
                                                for out_var_name in output_variables_name:
                                                    if out_var_name in input_var['value'] and out_var_name not in step_input_variables:
                                                        raise ValueError(f"Value should not refer to previous steps output variable names or TOOL_Output or sub_tasks directly, if the purpose is to derive the parameters input variable value from a previous steps output variable then parameter source field should be TOOL_Output with value as None in sub_task {subtasks_id}, Step {step_counter}")
                                                if input_var['source'] == "LLM_Generated" and input_var['value'] == "None":
                                                    raise ValueError(f"Value should not be 'None' for LLM_Generated source in sub_task {subtasks_id}, Step {step_counter}")
                                                elif input_var['source'] == "TOOL_Output" and input_var['value'] != "None":
                                                    raise ValueError(f"Value should be 'None' for TOOL_Output source in sub_task {subtasks_id}, Step {step_counter}")
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Value' for input variable in sub_task {subtasks_id}, Step {step_counter}")

                                            input_var['dependencies'] = []
                                            if "TOOL_Output" in input_var['source']:
                                                match = re.fullmatch(r"TOOL_Output\s*\(sub_task\s+(\d+),\s*Step\s+(\d+)\)", input_var['source'])
                                                if match:
                                                    dependent_subtask = int(match.group(1))
                                                    dependent_step = int(match.group(2))
                                                    subtasks_interdependencies_found = not(dependent_subtask == subtasks_id) or subtasks_interdependencies_found
                                                    input_var['dependencies'].append({
                                                        "sub_task": dependent_subtask,
                                                        "step": dependent_step
                                                    })
                                                    if dependent_subtask in execution_blueprints[current_group]:
                                                        if dependent_step in execution_blueprints[current_group][dependent_subtask]["steps"]:
                                                            used_step = execution_blueprints[current_group][dependent_subtask]["steps"][dependent_step]
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
                                            j += 1 
                                    
                                    if len(reqd_params_for_this_tool) != 0:
                                        raise ValueError(f"You have not used some of the required input parameters for tool name: {current_step['tool']}, like {reqd_params_for_this_tool}.")
                                elif line.startswith("- Output Variables:"):
                                    j += 1
                                    while j < len(group_lines):
                                        j = skip_empty_lines(group_lines, j)
                                        if j >= len(group_lines):
                                            break
                                        line = group_lines[j].strip()
                                        if line.startswith("Step") or line.startswith("execution_blueprint for sub_task") or line.startswith("Group"):
                                            break
                                        if line.startswith("- Name:"):
                                            output_var = {}
                                            output_var['name'] = line.split("Name:")[1].strip()
                                            output_variables_name.append(output_var['name'])
                                            j += 1

                                            j = skip_empty_lines(group_lines, j)
                                            if j >= len(group_lines):
                                                raise ValueError(f"Unexpected end of input while parsing output variable in sub_task {subtasks_id}, Step {step_counter}")

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
                                            j += 1  
                                else:
                                    j += 1  

                            steps[step_counter] = current_step
                        else:
                            j += 1  

                else:
                    j += 1  

            if not(modified_execution_blueprint_bool) and len(subtasks_in_group) > 1 and not subtasks_interdependencies_found:
                raise ValueError(f"Not all sub_tasks have interdependencies in Group {current_group}. Please put them in different groups if no interdependencies are there.")

        return chain_of_thought, execution_blueprints
    
    def parse_status_assistance_output(self, updated_execution_blueprint):
        result = {
            'chain_of_thought': '',
            'chosen_action': '',
            'execution_blueprint': None  
        }

        sections = re.split(r'\$\$CHAIN_OF_THOUGHT\$\$|\$\$CHOSEN_ACTION\$\$|\$\$EXECUTION_BLUEPRINT\$\$', updated_execution_blueprint)

        if len(sections) < 3:
            raise ValueError("The output must contain $$CHAIN_OF_THOUGHT$$ and $$CHOSEN_ACTION$$ sections.")

        result['chain_of_thought'] = sections[1].strip()

        chosen_action_text = sections[2].strip()
        if "MODIFY" in chosen_action_text:
            result['chosen_action'] = 'MODIFY'
        elif "DROP_SUBTASK" in chosen_action_text:
            result['chosen_action'] = 'DROP_SUBTASK'
        else:
            raise ValueError("The $$CHOSEN_ACTION$$ section must specify either MODIFY or DROP_SUBTASK.")

        if result['chosen_action'] == 'MODIFY':
            if len(sections) < 4:
                raise ValueError("The output must contain a $$EXECUTION_BLUEPRINT$$ section if MODIFY is chosen.")
            execution_blueprint_text = sections[3].strip()

            dummy_chain_of_thought = "$$CHAIN_OF_THOUGHT$$\nFiller space"
            full_execution_blueprint_text = f"{dummy_chain_of_thought}\n$$EXECUTION_BLUEPRINT$$\n{execution_blueprint_text}"

            _, result['execution_blueprint'] = self.parse_dag_compiler_execution_blueprint(full_execution_blueprint_text, modified_execution_blueprint_bool = True)

        return result

    
    def create_first_input_data(self,query, subtask_list):
        """
        Creates structured input data based on the query, subtask, and available Tools.
        Returns both a data structure and a formatted string.
        """
        note_string = """
                        1. Never substitute a literal variable name for the data itself: if a parameter input variable should be derived from a previous step’s output variable, do not set the parameter Source field as LLM_Generated that merely echoes the variable name it the Value field (remember the wrong examples show in the - Source of Inputs:, do not repeat it). Information must be passed between steps by supplying the actual data stored in output variable by setting the Source field as TOOL_Output (sub_task X, Step Y). 
                        2. Do not hallucinate or make up dummy data to fill in the values of input parameters, ground your data using relevant other tools (like perplexity, etc) and then pass on the information by setting the parameter source field as TOOL_Output (sub_task X, Step Y) of the future steps which will be dependent on the sub_task X, Step Y's output. 3. Use the method shown for handling caseswhere more than one previous step output dependencies are needed for a input parameter, instead of doing separate dummy (No tool, local merge step) like steps for cmobining data, instead you can simply use the method shown. 
                        3. For any SQL task, first list the schema of all the public tables, and only afterwards carry out the required operations. Do not hallucinate the table names or schemas, first ground your knowledge by following this.
                        4. The numbering of the steps for each sub task starts from 1 always.
                      """
        formatted_string = f"**Query:** \"{query}\"\n\n Important Note:{note_string}\n\n**TaskDecomposers's sub_task Requests:**\n"

        unique_tools = {}

        for subtask in subtask_list:
            formatted_string += f"{subtask['instance_id']}. sub_task {subtask['instance_id']}: {subtask['subtask_description']}\n"
            formatted_string += f"Details: {subtask['request']['description']}"
            formatted_string += "\nList of Relevant TOOls:\n"

            for tool in subtask['request']['relevant_tools']:
                formatted_string += f"   - {tool['tool_name']}\n"

                if tool['tool_name'] not in unique_tools:
                    unique_tools[tool['tool_name']] = {
                        "Use": tool.get('Use', 'N/A')
                    }
            formatted_string += "\n"  

        self.unique_tools = unique_tools

        formatted_string += "**Description of Tools:**\n"
        tool_id = 1
        for tool_name, tool_details in unique_tools.items():
            if tool_name in RAPIDAPI_TOOLS_DICT:
                formatted_string += (
                    f"{tool_id}. {tool_name}\n"
                    f"   - **Use:** {tool_details['Use']}\n\n"
                    f"   - **Documentation:** {RAPIDAPI_TOOLS_DICT[tool_name]}\n\n"
                    f"   - **Required Parameters (If not specified then error will be raised):** {RAPIDAPI_REQD_PARAMS_DICT[tool_name]}\n\n"
                )
            elif tool_name in FUNCTION_TOOLS_DOCUMENTATION_DICT:
                formatted_string += (
                    f"{tool_id}. {tool_name}\n"
                    f"   - **Use:** {tool_details['Use']}\n\n"
                    f"   - **Documentation:** {FUNCTION_TOOLS_DOCUMENTATION_DICT[tool_name]}\n\n"
                    f"   - **Required Parameters (If not specified then error will be raised):** {FUNCTION_TOOLS_REQD_PARAMS_DICT[tool_name]}\n\n"
                )
            elif tool_name in self.MCP_PARAMS_DICT:
                print(self.MCP_PARAMS_DICT)
                print(tool_name)
                try:
                    required_params = self.MCP_PARAMS_DICT[tool_name]['parameters_dict'].get('required', '')
                except:
                    required_params = ""
                formatted_string += (
                    f"{tool_id}. {tool_name}\n"
                    f"   - **Use:** {self.MCP_PARAMS_DICT[tool_name]['documentation']}\n\n"
                    f"   - **Documentation:** {self.MCP_PARAMS_DICT[tool_name]['parameters']}\n\n"
                    f"   - **Required Parameters (If not specified then error will be raised):** "
                    f"{required_params}\n\n"
                )
            else:
                raise ValueError(f"Invalid TOOL Name {tool_name}. It is not there in RAPIDAPI_TOOLS_DICT or FUNCTION_APIS_FUNCTION_DICT. This error is inside create_first_input_data")
            tool_id += 1

        return formatted_string
    
    def make_input_status_update(self, group_execution_blueprint_dict, group_no, status_update_dict):
        result = []

        result.append(f"Group execution_blueprint:\n")

        result.append(f"\nGroup {group_no}:\n")

        for subtask_no, subtask_data in group_execution_blueprint_dict.items():
            result.append(f"execution_blueprint for sub_task {subtask_no}:\n")
            result.append(f"sub_task Description: {subtask_data['subtask_description']}\n")
            result.append("\nexecution_blueprint Steps:\n")

            for step_no, step_data in subtask_data['steps'].items():
                result.append(f"Step {step_no}")
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

            result.append("\n")  

        if hasattr(self, 'unique_tools'):
            result.append("Available TOOL Descriptions:\n")
            tool_id = 1
            for tool_name, tool_details in self.unique_tools.items():
                if tool_name in RAPIDAPI_TOOLS_DICT:
                    result.append(f"{tool_id}. {tool_name}")
                    result.append(f"   - **Use:** {tool_details['Use']}\n")
                    result.append(f"   - **Documentation:** {RAPIDAPI_TOOLS_DICT[tool_name]}\n")
                    tool_id += 1
                elif tool_name in FUNCTION_TOOLS_DOCUMENTATION_DICT:
                    result.append(f"{tool_id}. {tool_name}")
                    result.append(f"   - **Use:** {tool_details['Use']}\n")
                    result.append(f"   - **Documentation:** {FUNCTION_TOOLS_DOCUMENTATION_DICT[tool_name]}\n")
                    tool_id += 1
                elif tool_name in self.MCP_PARAMS_DICT:
                    print(self.MCP_PARAMS_DICT)
                    print(tool_name)
                    formatted_string = (
                        f"{tool_id}. {tool_name}\n"
                        f"   - **Use:** {self.MCP_PARAMS_DICT[tool_name]['documentation']}\n\n"
                        f"   - **Documentation:** {self.MCP_PARAMS_DICT[tool_name]['parameters']}\n\n"
                    )
                    result.append(formatted_string)
                    tool_id += 1
                else:
                    raise ValueError(f"Invalid TOOL Name {tool_name}. It is not there in RAPIDAPI_TOOLS_DICT or FUNCTION_APIS_FUNCTION_DICT.")
            result.append("\n")  

        result.append("Status Update:\n")
        result.append(status_update_dict['status_update'])

        result.append("\nAssistance Request:\n")
        result.append(status_update_dict['assistance_request'])

        return "\n".join(result)

    ########################
    def setup(self, query, subtask_list):
        self.subtask_list = subtask_list
        # Logic to create execution_blueprint and initialize agent instances
        # We can use self.chat_history to provide context
        formatted_string = self.create_first_input_data(query, subtask_list)
        print("\nformatted_string : \n",formatted_string)

        self.chat_history.append({"role": "user", "content": self.execution_blueprint_creation_prompt}) 
        self.chat_history.append({"role": "user", "content": formatted_string})
        run_success = False
        counter = 0
        while not run_success and counter < 5:
            try:
                llm_response_execution_blueprint = self.generate()
                print("llm_response_execution_blueprint before self reflection : \n",llm_response_execution_blueprint)
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
            
        with open("execution_blueprint.json", "w") as json_file:
            json.dump(execution_blueprint_dict, json_file, indent=4)
        with open("execution_blueprint.json", "r") as json_file:
            execution_blueprint_dict = json.load(json_file)
        self.execution_blueprint = execution_blueprint_dict
        return execution_blueprint_dict


    async def communicate(self, update, agent_id, agent_object):
        await self.queue.put((update, agent_id, agent_object))
        
    async def process_queue(self):
        while True:
            status_update_dict, agent_id, agent_object = await self.queue.get()
            print("status_update_dict:", status_update_dict)
            
            print(f"Processing update from Agent {agent_id}")
            
            try:
                status_assistance_llm_input = self.make_input_status_update(
                    self.execution_blueprint[str(agent_object.group_id)], 
                    agent_object.group_id, 
                    status_update_dict
                )
            except Exception as e:
                print("ERROR in make_input_status_update:")
                traceback.print_exc()  
                continue


            print("status_assistance_llm_input:", status_assistance_llm_input)

            self.chat_history.append({"role": "user", "content": self.status_assistance_prompt}) 
            self.chat_history.append({"role": "user", "content": status_assistance_llm_input})

            run_success = False
            counter = 0
            while not run_success and counter < 5:
                counter += 1
                try:
                    updated_execution_blueprint = await asyncio.to_thread(self.generate, True)
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
                async with self.lock:

                    agent_object.drop = True
                print('Sent Request to Drop sub_task')

            elif parsed_updated_execution_blueprint['chosen_action'] == "MODIFY":
                updated_execution_blueprint_dict = await asyncio.to_thread(
                    self.save_and_load_execution_blueprint, 
                    agent_object.group_id, 
                    parsed_updated_execution_blueprint['execution_blueprint']
                )
                print("updated_execution_blueprint_dict after loading:", updated_execution_blueprint_dict)
                async with self.lock:
                    agent_object.group_execution_blueprint = updated_execution_blueprint_dict
                    agent_object.modify = True
                print('Sent Request to Modify sub_task')

            else:
                print("In the else statement")
                raise ValueError("The chosen_action key must specify either MODIFY or DROP_SUBTASK.")
            
            print(f"Finished processing update from Agent {agent_id}")
            
            await asyncio.sleep(0.1) 

    def save_and_load_execution_blueprint(self, group_id, execution_blueprint):
        filename = f"execution_blueprint_updated_group_{group_id}.json"
        with open(filename, "w") as json_file:
            json.dump(execution_blueprint, json_file, indent=4)
        with open(filename, "r") as json_file:
            updated_execution_blueprint_dict = json.load(json_file)
        self.execution_blueprint[str(group_id)] = updated_execution_blueprint_dict[str(group_id)]
        return updated_execution_blueprint_dict