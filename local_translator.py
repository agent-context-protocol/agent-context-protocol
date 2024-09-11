from base import BaseNode
from available_apis.hardcoded_format.perplexity import PERPLEXITY_CHAT_COMPLETIONS_DOCS

class LocalTranslatorNode(BaseNode):
    def __init__(self, node_id, panel_description, system_prompt=None):
        super().__init__(node_id, system_prompt)
        self.panel_description = panel_description
        self.workflow = None

    def get_system_prompts(self):
        # workflow_creation_prompt
        with open('prompts/local_translator/local_translator_system_prompt.txt', 'r') as file:
            self.workflow_finalization_prompt = file.read()

    # input format prep functions
    def prepare_input_for_step(self, step, api_documentation):
        """
        Prepare the input for a single step in the workflow.
        
        Args:
            step (dict): The workflow step that contains the API details, input vars, output vars, etc.
            api_description (dict): The API description (loaded from a dictionary based on API name).
            
        Returns:
            dict: The prepared input data for the API request.
        """
        input_string = "\nPlease generate output for this input:\n"
        input_string += "API Details:\n"

        input_string += f"Step No: {step['step']}\n"
        input_string += f"API: {step['api']}\n"
        input_string += f"Handles: {step['handles']}\n"
        input_string += f"Input Variable: {step['input_vars']} (Description: {step['input_desc']})\n"
        input_string += f"Output Variable: {step['output_vars']} (Description: {step['output_desc']})\n"

        # Add dependencies if any
        if step.get("dependencies"):
            dependencies_str = ', '.join([f"Panel {d['panel']}, Step {d['step']}" for d in step['dependencies']])
            input_string += f"Dependencies: {dependencies_str}\n"
        else:
            input_string += "Dependencies: None\n"

        # Add the API documentation provided
        input_string += "\nAPI Documentation:\n"
        input_string += api_documentation
        
        return input_string

    def build_verify(self, api_descriptions = None):
        """
        This function goes through each step of the workflow and prepares inputs based on the workflow details
        and the API descriptions provided.
        
        Args:
            api_descriptions (dict): Dictionary where the key is the API name and the value is the API description.
        """
        if not self.workflow:
            raise ValueError("No workflow found for this panel.")
        
        for step in self.workflow:
            print(f"Processing Step {step['step']} for API: {step['api']}")
            # Call the function to prepare the input for the current step
            # input_data = self.prepare_input_for_step(step, api_descriptions[step["api"]])
            input_data = self.prepare_input_for_step(step, PERPLEXITY_CHAT_COMPLETIONS_DOCS)
            print(f"Prepared input for step {step['step']}: {input_data}")
            
