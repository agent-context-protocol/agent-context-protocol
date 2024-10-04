from base import BaseNode
import re
import json
import asyncio
from available_apis.rapid_apis_format.return_dict import RAPID_APIS_DICT
from available_apis.function_format.return_dict import FUNCTION_APIS_DOCUMENTATION_DICT

class MainTranslatorNode(BaseNode):
    def __init__(self, node_name, system_prompt = None):
        super().__init__(node_name, system_prompt)
        self.get_system_prompts()
        self.clusters = {}
        self.lock = asyncio.Lock()
        self.queue = asyncio.Queue()
        self.workflow = None

        self.unique_apis = {}

    def get_system_prompts(self):
        # workflow_creation_prompt
        with open('prompts/main_translator/workflow_creation_prompt.txt', 'r') as file:
            self.workflow_creation_prompt = file.read()

        # workflow_creation_prompt
        with open('prompts/main_translator/status_assistance_prompt.txt', 'r') as file:
            self.status_assistance_prompt = file.read()

    ########################
    # ALL THE PARSING FUNCTIONS WILL BE HERE

    def parse_main_translator_workflow(self, text, restrict_one_group = False):
        # First, split the text into CHAIN_OF_THOUGHT and WORKFLOW sections
        sections = re.split(r"\$\$WORKFLOW\$\$", text)
        if len(sections) != 2:
            raise ValueError("The text does not contain exactly one CHAIN_OF_THOUGHT and one WORKFLOW section.")

        chain_of_thought_text = sections[0].replace("$$CHAIN_OF_THOUGHT$$", "").strip()
        workflow_text = sections[1].strip()

        # Extract the CHAIN_OF_THOUGHT
        chain_of_thought = chain_of_thought_text

        # Helper function to skip empty lines
        def skip_empty_lines(lines, index):
            while index < len(lines) and not lines[index].strip():
                index += 1
            return index

        # Now parse the WORKFLOW section
        # Split based on "Group X:" separator
        group_blocks = re.split(r"(Group \d+:)", workflow_text)
        workflows = {}

        for i in range(1, len(group_blocks), 2):
            group_header = group_blocks[i]
            group_content = group_blocks[i + 1]

            # Extract group number
            current_group = int(re.search(r'\d+', group_header).group(0))
            workflows[current_group] = {}

            group_lines = group_content.strip().split('\n')
            panels_in_group = []
            interdependencies_found = False

            j = 0
            while j < len(group_lines):
                # Skip empty lines
                j = skip_empty_lines(group_lines, j)
                if j >= len(group_lines):
                    break

                line = group_lines[j].strip()

                if line.startswith("Workflow for Panel"):
                    # Extract panel ID
                    panel_id = int(re.search(r'\d+', line).group(0))
                    workflows[current_group][panel_id] = {"panel_description": None, "steps": {}}
                    steps = workflows[current_group][panel_id]["steps"]
                    panels_in_group.append(panel_id)
                    j += 1

                    # Skip empty lines
                    j = skip_empty_lines(group_lines, j)
                    if j >= len(group_lines):
                        raise ValueError(f"Missing content after 'Workflow for Panel {panel_id}'")

                    # Parse Panel Description
                    if group_lines[j].strip().startswith("Panel Description:"):
                        panel_desc = group_lines[j].split("Panel Description:")[1].strip()
                        workflows[current_group][panel_id]["panel_description"] = panel_desc
                        j += 1
                    else:
                        raise ValueError(f"Missing Panel Description for Panel {panel_id}")

                    # Skip empty lines
                    j = skip_empty_lines(group_lines, j)
                    if j >= len(group_lines):
                        raise ValueError(f"Missing content after Panel Description for Panel {panel_id}")

                    # Check for 'Workflow Steps:'
                    if group_lines[j].strip() == "Workflow Steps:":
                        j += 1
                    else:
                        raise ValueError(f"Missing 'Workflow Steps:' section for Panel {panel_id}")

                    # Parse Steps
                    while j < len(group_lines):
                        # Skip empty lines
                        j = skip_empty_lines(group_lines, j)
                        if j >= len(group_lines):
                            break

                        line = group_lines[j].strip()
                        if line.startswith("Workflow for Panel") or line.startswith("Group"):
                            break  # Move to the next panel or group

                        # Parse Step
                        if line.startswith("Step"):
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
                                if line.startswith("Step") or line.startswith("Workflow for Panel") or line.startswith("Group"):
                                    break  # Next step, panel, or group

                                if line.startswith("- API:"):
                                    current_step['api'] = line.split("- API:")[1].strip()
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
                                        if line.startswith("- Output Variables:") or line.startswith("Step") or line.startswith("Workflow for Panel") or line.startswith("Group"):
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
                                                    interdependencies_found = True
                                                    dependent_panel = int(match.group(1))
                                                    dependent_step = int(match.group(2))
                                                    input_var['dependencies'].append({
                                                        "panel": dependent_panel,
                                                        "step": dependent_step
                                                    })
                                                    # Go to the referenced panel and step in workflows to update "used_by"
                                                    if dependent_panel in workflows[current_group]:
                                                        if dependent_step in workflows[current_group][dependent_panel]["steps"]:
                                                            used_step = workflows[current_group][dependent_panel]["steps"][dependent_step]
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
                                                                raise ValueError(f"In Step {dependent_step} Panel {dependent_panel}, dependent input variable has a different name")
                                                        else:
                                                            raise ValueError(f"Step {dependent_step} not found in Panel {dependent_panel}")
                                                    else:
                                                        raise ValueError(f"Panel {dependent_panel} not found in Group {current_group}.")
                                                else:
                                                    raise ValueError(f"Invalid source format for dependencies in Panel {panel_id}, Step {step_counter}")
                                            current_step['input_vars'].append(input_var)
                                        else:
                                            j += 1  # Skip any lines that are not input variables
                                elif line.startswith("- Output Variables:"):
                                    j += 1
                                    while j < len(group_lines):
                                        # Skip empty lines
                                        j = skip_empty_lines(group_lines, j)
                                        if j >= len(group_lines):
                                            break
                                        line = group_lines[j].strip()
                                        if line.startswith("Step") or line.startswith("Workflow for Panel") or line.startswith("Group"):
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

            # Check for interdependencies
            if len(panels_in_group) > 1 and not interdependencies_found:
                raise ValueError(f"No interdependencies found in Group {current_group} despite having multiple panels.")

        # Return the chain_of_thought and workflows
        return chain_of_thought, workflows
    
    def parse_status_assistance_output(self, updated_workflow):
        # Initialize the result dictionary
        result = {
            'chain_of_thought': '',
            'chosen_action': '',
            'workflow': None  # This will only be filled if the chosen action is MODIFY
        }

        # Split the input string into sections using regular expressions
        sections = re.split(r'\$\$CHAIN_OF_THOUGHT\$\$|\$\$CHOSEN_ACTION\$\$|\$\$WORKFLOW\$\$', updated_workflow)

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

        # If the action is MODIFY, we should also parse the workflow section
        if result['chosen_action'] == 'MODIFY':
            if len(sections) < 4:
                raise ValueError("The output must contain a $$WORKFLOW$$ section if MODIFY is chosen.")
            workflow_text = sections[3].strip()

            # Parse the workflow section by passing it to the existing workflow parser
            dummy_chain_of_thought = "$$CHAIN_OF_THOUGHT$$\nFiller space"
            full_workflow_text = f"{dummy_chain_of_thought}\n$$WORKFLOW$$\n{workflow_text}"

            # Call the existing workflow parser and save the parsed workflow
            _, result['workflow'] = self.parse_main_translator_workflow(full_workflow_text)

        return result







        
    ########################
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
            formatted_string += f"{panel['instance_id']}. Panel {panel['instance_id']}: {panel['panel_description']}\n"
            formatted_string += "List of Relevant APIs:\n"

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
                )
            elif api_name in FUNCTION_APIS_DOCUMENTATION_DICT:
                formatted_string += (
                    f"{api_id}. {api_name}\n"
                    f"   - **Use:** {api_details['Use']}\n\n"
                    f"   - **Documentation:** {FUNCTION_APIS_DOCUMENTATION_DICT[api_name]}\n\n"
                )
            else:
                raise ValueError(f"Invalid API Name {api_name}. It is not there in RAPID_APIS_DICT or FUNCTION_APIS_FUNCTION_DICT. This error is inside create_first_input_data")
            api_id += 1

        return formatted_string
    
    def make_input_status_update(self, group_workflow_dict, status_update_dict):
        result = []

        # Add Group Workflow header
        result.append("Group Workflow:\n")

        # Process each panel's workflow
        for panel_no, panel_data in group_workflow_dict.items():
            result.append(f"Workflow for Panel {panel_no}:\n")
            result.append(f"Panel Description: {panel_data['panel_description']}\n")
            result.append("\nWorkflow Steps:\n")

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

            result.append("\n")  # Add spacing between workflows

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
                    raise ValueError(f"Invalid API Name {api_name}. It is not there in RAPID_APIS_DICT or FUNCTION_APIS_FUNCTION_DICT. This error is inside create_first_input_data")
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
        # Logic to create workflow and initialize local translator instances
        # We can use self.chat_history to provide context
        formatted_string = self.create_first_input_data(query, panels_list)
        print("\nformatted_string : \n",formatted_string)

        # generating the workflow from the LLM
        self.chat_history.append({"role": "user", "content": self.workflow_creation_prompt}) # system prompt for workflow_creation
        self.chat_history.append({"role": "user", "content": formatted_string})
        run_success = False
        counter = 0
        while not run_success and counter < 5:
            try:
                llm_response_workflow = self.generate()
                llm_response_workflow = llm_response_workflow.replace("**", "")
                llm_response_workflow = llm_response_workflow.replace("`", "")
                print("llm_response_workflow : \n",llm_response_workflow)
                _, workflow_dict = self.parse_main_translator_workflow(llm_response_workflow)
                run_success = True
            except Exception as e:
                error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT and WORKFLOW without any other details before or after.:\n {str(e)}' 
                self.chat_history.append({"role": "user", "content": error_message})
                print("error_message : ",error_message)
            
            counter += 1
        
        if not run_success:
            raise ValueError("SOmething is wrong with the LLM or the parsing main translator workflow. An error is not expected here")
            
        print("\llm_response_workflow:\n")
        print(llm_response_workflow)
        # print("\nworkflows:\n")
        # print(workflow_dict)
        # Write to a JSON file
        with open("workflow.json", "w") as json_file:
            json.dump(workflow_dict, json_file, indent=4)
        self.workflow = workflow_dict
        return workflow_dict
    
    async def communicate(self, update, local_translator_id, local_translator_object):
        await self.queue.put((update, local_translator_id, local_translator_object))
        
    async def process_queue(self):
        while True:
            async with self.lock:
                if self.queue.empty():
                    await asyncio.sleep(0.1)
                    continue
                status_update_dict, local_translator_id, local_translator_object = await self.queue.get()
                print("status_update_dict : ",status_update_dict)
                
                # Process the update here
                # This is where you'd put the logic to handle the communication
                print(f"Processing update from Local Translator {local_translator_id}")

                # Simulate some processing time
                await asyncio.sleep(1)

                status_assistance_llm_input = self.make_input_status_update(local_translator_object.group_workflow, status_update_dict)

                # generating the workflow from the LLM
                self.chat_history.append({"role": "user", "content": self.status_assistance_prompt}) # system prompt for workflow_creation
                self.chat_history.append({"role": "user", "content": status_assistance_llm_input})

                run_success = False
                counter = 0
                while not run_success and counter < 5:
                    counter += 1
                    try:
                        updated_workflow = self.generate()
                        updated_workflow = updated_workflow.replace("**", "")
                        updated_workflow = updated_workflow.replace("`", "")
                        print("updated_workflow : ",updated_workflow)
                        parsed_updated_workflow = self.parse_status_assistance_output(updated_workflow)
                        print("parsed_updated_workflow : ", parsed_updated_workflow)
                        run_success = True
                    except Exception as e:
                        error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT, CHOSEN_ACTION and/or WORKFLOW without any other details before or after.:\n {str(e)}' 
                        self.chat_history.append({"role": "user", "content": error_message})
                        print("error_message : ",error_message)

                if not run_success:
                    raise ValueError("Something is wrong with the LLM or the parsing status_assistance in main translator. An error is not expected here")

                if parsed_updated_workflow['chosen_action'] == "DROP_PANEL":
                    local_translator_object.drop = True
                    print('Sent Request to Drop Panel')
                elif parsed_updated_workflow['chosen_action'] == "MODIFY":
                    local_translator_object.modify = True
                    with open(f"updated_workflow_group_{local_translator_object.group_id}.json", "w") as json_file:
                        json.dump(parsed_updated_workflow['workflow'], json_file, indent=4)
                    with open("workflow.json", "r") as json_file:
                        updated_workflow_dict = json.load(json_file)
                    local_translator_object.group_workflow = updated_workflow_dict
                else:
                    raise ValueError("The chosen_action key must specify either MODIFY or DROP_PANEL.")
                
                print(f"Finished processing update from Local Translator {local_translator_id}")
            
            # Release the lock and allow a short time for other tasks to acquire it
            await asyncio.sleep(0.1)