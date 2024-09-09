from base import BaseNode
import re

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
        group_blocks = text.split('---')  # Split based on groups, as now we have groups
        workflows = {}

        current_group = None

        for group_block in group_blocks:
            group_lines = group_block.strip().split('\n')
            panel_id = None
            panel_desc = None
            steps = []
            current_step = {}

            for line in group_lines:
                line = line.strip()

                # Start parsing group if "Group X" is mentioned
                if line.startswith("**Group"):
                    current_group = re.search(r'\d+', line).group(0)
                    workflows[current_group] = {}  # Initialize group in workflows

                # Start parsing workflow for panels
                elif line.startswith("**Workflow for Panel"):
                    panel_id = re.search(r'\d+', line).group(0)
                    workflows[current_group][panel_id] = {
                        "panel_description": None,
                        "steps": []
                    }  # Initialize panel data for the group

                elif line.startswith("**Panel Description:**"):
                    panel_desc = line.split("**Panel Description:**")[1].strip()
                    if not panel_desc:
                        raise ValueError(f"Missing panel description for Panel {panel_id}")
                    workflows[current_group][panel_id]["panel_description"] = panel_desc

                elif line.startswith("**Step"):
                    if current_step:
                        steps.append(current_step)
                    current_step = {}
                    current_step['step'] = re.search(r'\d+', line).group(0)  # Extract step number

                elif line.startswith("- **API:**"):
                    api_data = line.split("- **API:**")[1].strip()
                    if not api_data:
                        raise ValueError(f"Missing API data for Panel {panel_id}, Step {current_step['step']}")
                    current_step['api'] = api_data

                elif line.startswith("- **Handles:**"):
                    handles_data = line.split("- **Handles:**")[1].strip()
                    if not handles_data:
                        raise ValueError(f"Missing Handles data for Panel {panel_id}, Step {current_step['step']}")
                    current_step['handles'] = handles_data

                elif line.startswith("- **Input:**"):
                    input_match = re.findall(r"`(.*?)`", line)
                    input_vars = input_match[0]  # Extract the variable name inside backticks
                    if not input_vars:
                        raise ValueError(f"Missing Input Variable for Panel {panel_id}, Step {current_step['step']}")
                    input_desc = line.split('(')[1].split(')')[0]  # Extract description inside parentheses
                    if not input_desc:
                        raise ValueError(f"Missing Input Variable Description for Panel {panel_id}, Step {current_step['step']}")
                    current_step['input_vars'] = input_vars
                    current_step['input_desc'] = input_desc

                elif line.startswith("- **Output:**"):
                    output_match = re.findall(r"`(.*?)`", line)
                    output_vars = output_match[0]  # Extract the variable name inside backticks
                    if not output_vars:
                        raise ValueError(f"Missing Output Variable for Panel {panel_id}, Step {current_step['step']}")
                    output_desc = line.split('(')[1].split(')')[0]  # Extract description inside parentheses
                    if not output_desc:
                        raise ValueError(f"Missing Output Variable Description for Panel {panel_id}, Step {current_step['step']}")
                    current_step['output_vars'] = output_vars
                    current_step['output_desc'] = output_desc

                elif line.startswith("- **Dependencies:**"):
                    # Handle both single and multiple dependencies
                    dependencies_text = line.split("- **Dependencies:**")[1].strip()
                    if dependencies_text == "None":
                        current_step['dependencies'] = None
                    else:
                        dependencies = []
                        # If multiple dependencies are present, split by commas
                        dep_list = dependencies_text.split(',')
                        for dep in dep_list:
                            dep_clean = dep.strip()
                            match = re.search(r'Panel (\d+) Step (\d+)', dep_clean)
                            if match:
                                panel_num = match.group(1)
                                step_num = match.group(2)
                                dependencies.append({"panel": panel_num, "step": step_num})
                            else:
                                raise ValueError(f"Unparsed or invalid dependency in Panel {panel_id}, Step {current_step['step']}: {dep_clean}")
                        if dependencies_text and not dependencies:
                            raise ValueError(f"Dependencies text exists but no dependencies parsed for Panel {panel_id}, Step {current_step['step']}")
                        current_step['dependencies'] = dependencies

            if current_step:
                steps.append(current_step)

            if panel_id:
                workflows[current_group][panel_id]["steps"] = steps

        return workflows #, variable_details  # Return both the workflows and the variables details

    
    ########################
    # ALL THE CREATING INPUT FOR LLM FUNCTIONS WILL BE HERE
    
    # create input string
    def create_first_input_data(self, query, panels_list):
        """
        Creates structured input data based on the query, panels, and available APIs.
        Returns both a data structure and a formatted string.
        """
        # Create the string format
        formatted_string = f"**Query:** \"{query}\"\n\n**Interpreter's Panel Requests:**\n"
        
        # Adding panel requests
        for panel in panels_list:
            formatted_string += f"{panel['instance_id']}. Panel {panel['instance_id']}: {panel['request']['description']}\n"
        
            formatted_string += "\n**List of Available APIs:**\n"

        # Adding available APIs with their input, output, and use
            for api_id, api in enumerate(panel['request']['relevant_apis'], start=1):
                formatted_string += (
                    f"{api_id}. {api['api_name']}\n"
                    f"   - **Input:** {api.get('Input', 'N/A')}\n"
                    f"   - **Output:** {api.get('Output', 'N/A')}\n"
                    f"   - **Use:** {api.get('Use', 'N/A')}\n\n"
                )

        return formatted_string

    def setup(self, query, panels_list):
        # Logic to create workflow and initialize local translator instances
        # We can use self.chat_history to provide context
        formatted_string = self.create_first_input_data(query, panels_list)

        # generating the workflow from the LLM
        self.chat_history.append({"role": "system", "content": self.workflow_creation_prompt}) # system prompt for workflow_creation
        self.chat_history.append({"role": "user", "content": formatted_string})
        run_success = False
        counter = 0
        while not run_success and counter < 5:
            try:
                llm_response_workflow = self.generate()
                workflow_dict = self.parse_main_translator_workflow(llm_response_workflow)
                run_success = True
            except Exception as e:
                error_message = f'The format of the output is incorrect please rectify based on this error message and only output the workflow:\n {str(e)}' 
                self.chat_history.append({"role": "user", "content": error_message})
            
            counter += 1
        
        if not run_success:
            print("counter : ",counter)
            print(cause_error)
        # print(llm_response_workflow)
        print("\nworkflows:\n")
        print(workflow_dict)
        return workflow_dict