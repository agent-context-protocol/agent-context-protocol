from base import BaseNode
import re
import json

class MainTranslatorNode(BaseNode):
    def __init__(self, node_name, system_prompt = None):
        super().__init__(node_name, system_prompt)
        self.get_system_prompts()
        self.clusters = {}

    def get_system_prompts(self):
        # workflow_creation_prompt
        with open('prompts/main_translator/workflow_creation_prompt.txt', 'r') as file:
            self.workflow_creation_prompt = file.read()

    ########################
    # ALL THE PARSING FUNCTIONS WILL BE HERE

    def parse_main_translator_workflow(self, text):
        # First, split the text into CHAIN_OF_THOUGHT and WORKFLOW sections
        sections = re.split(r"\s*WORKFLOW\s*", text)
        if len(sections) != 2:
            raise ValueError("The text does not contain exactly one CHAIN_OF_THOUGHT and one WORKFLOW section.")

        chain_of_thought_text = sections[0].strip()
        workflow_text = sections[1].strip()

        # Extract the CHAIN_OF_THOUGHT
        match = re.search(r"CHAIN_OF_THOUGHT\s*(.*)", chain_of_thought_text, re.DOTALL)
        if match:
            chain_of_thought = match.group(1).strip()
        else:
            raise ValueError("CHAIN_OF_THOUGHT section not found or improperly formatted.")

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
                                        if line.startswith("- Name:") or line.startswith("  - Name:"):
                                            input_var = {}
                                            # Name
                                            input_var['name'] = line.split("Name:")[1].strip()
                                            j += 1

                                            # Skip empty lines
                                            j = skip_empty_lines(group_lines, j)
                                            if j >= len(group_lines):
                                                raise ValueError(f"Unexpected end of input while parsing input variable in Panel {panel_id}, Step {step_counter}")

                                            # Source
                                            line = group_lines[j].strip()
                                            if line.startswith("Source:"):
                                                input_var['source'] = line.split("Source:")[1].strip()
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Source' for input variable in Panel {panel_id}, Step {step_counter}")

                                            # Skip empty lines
                                            j = skip_empty_lines(group_lines, j)
                                            if j >= len(group_lines):
                                                raise ValueError(f"Unexpected end of input while parsing input variable in Panel {panel_id}, Step {step_counter}")

                                            # Description
                                            line = group_lines[j].strip()
                                            if line.startswith("Description:"):
                                                input_var['description'] = line.split("Description:")[1].strip()
                                                j += 1
                                            else:
                                                raise ValueError(f"Missing 'Description' for input variable in Panel {panel_id}, Step {step_counter}")

                                            # Handle dependencies
                                            input_var['dependencies'] = []
                                            if "API_Output" in input_var['source']:
                                                match = re.search(r"Panel (\d+), Step (\d+)", input_var['source'])
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
                                                            for output_var in used_step["output_vars"]:
                                                                if output_var["name"] == input_var['name']:
                                                                    if 'used_by' not in output_var:
                                                                        output_var['used_by'] = []
                                                                    output_var["used_by"].append({
                                                                        "panel": panel_id,
                                                                        "step": step_counter
                                                                    })
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
                                        if line.startswith("- Name:") or line.startswith("  - Name:"):
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
                                            if line.startswith("Description:"):
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
                        "Input": api.get('Input', 'N/A'),
                        "Output": api.get('Output', 'N/A'),
                        "Use": api.get('Use', 'N/A')
                    }
            formatted_string += "\n"  # Add a newline after each panel

        # Now add the full details of each unique API at the end
        formatted_string += "**Description of APIs:**\n"
        api_id = 1
        for api_name, api_details in unique_apis.items():
            formatted_string += (
                f"{api_id}. {api_name}\n"
                f"   - **Input:** {api_details['Input']}\n"
                f"   - **Output:** {api_details['Output']}\n"
                f"   - **Use:** {api_details['Use']}\n\n"
            )
            api_id += 1

        return formatted_string

    def setup(self, query, panels_list):
        # Logic to create workflow and initialize local translator instances
        # We can use self.chat_history to provide context
        formatted_string = self.create_first_input_data(query, panels_list)
        print("\nformatted_string : \n",formatted_string)

        # generating the workflow from the LLM
        self.chat_history.append({"role": "system", "content": self.workflow_creation_prompt}) # system prompt for workflow_creation
        self.chat_history.append({"role": "user", "content": formatted_string})
        run_success = False
        counter = 0
        while not run_success and counter < 5:
            try:
                llm_response_workflow = self.generate()
                print("llm_response_workflow : \n",llm_response_workflow)
                _, workflow_dict = self.parse_main_translator_workflow(llm_response_workflow)
                run_success = True
            except Exception as e:
                error_message = f'The format of the output is incorrect please rectify based on this error message, only output the CHAIN_OF_THOUGHT and WORKFLOW without any other details before or after.:\n {str(e)}' 
                self.chat_history.append({"role": "user", "content": error_message})
                print("error_message : ",error_message)
            
            counter += 1
        
        if not run_success:
            print("counter : ",counter)
            print(cause_error)
            
        print("\llm_response_workflow:\n")
        print(llm_response_workflow)
        # print("\nworkflows:\n")
        # print(workflow_dict)
        # Write to a JSON file
        with open("workflow.json", "w") as json_file:
            json.dump(workflow_dict, json_file, indent=4)
        return workflow_dict