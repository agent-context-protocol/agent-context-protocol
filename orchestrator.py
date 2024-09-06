# main_orchestrator.py
# from interpreter import InterpreterNode
from main_translator import MainTranslatorNode
from local_translator import LocalTranslatorNode

class MainOrchestrator:
    def __init__(self):
        self.get_system_prompts()
        # self.interpreter = InterpreterNode('interpreter')
        self.main_translator = MainTranslatorNode('main_translator', self.main_translator_system_prompt)
        self.local_translators = {}

    def get_system_prompts(self):
        # Interpreter system prompt
        # self.interpreter_system_prompt = 

        # Main Translator System Prompt
        with open('prompts/main_translator/main_translator_system_prompt.txt', 'r') as file:
            self.main_translator_system_prompt = file.read()
        
        # Local Translator System Prompt
        # self.local_translator_system_prompt = 

    def run(self, user_query):
        # Send user query to interpreter
        # self.interpreter.user_query = user_query

        # # Get initial setup from interpreter and send to main translator
        # initial_setup = self.interpreter.setup()
        query = "What are the best vacation spots in India and their average temperatures?"
        panels_list = [
            "Best Places for Vacation in India",
            "A Graph of Average Temperature in the Top 10 Places"
        ]
        available_apis = {
            "Perplexity": {
                "input": "A simple query that requires searching the web.",
                "output": "A compiled answer based on web search results.",
                "use": "As a search engine to retrieve and synthesize information from multiple sources into a single, concise response."
            },
            "PlotAgent": {
                "input": "A query along with a response from Perplexity.",
                "output": "If plots are generated, it returns the location where plots are saved and a plot explanation string; otherwise, it returns 'Fail.'",
                "use": "For queries that can be visualized through graphs or charts. If initial information is insufficient, it triggers a Perplexity search for more data."
            },
            "TextToImage": {
                "input": "A query along with a response from Perplexity.",
                "output": "A location where the image generated based on the input prompt is saved.",
                "use": "For creating visually compelling illustrations or images that enhance and complement the response."
            }
        }
        message = self.main_translator.setup(query, panels_list, available_apis)
        # group_data_structure =  create_groups(message) 
        # setup_message = group_data_structure.setup()
        # confirmation = self.main_translator.communicate(setup_message)
        # group_data_structure.recieve_confirmation = 

        # # Main loop
        # while True:
        #     # Process messages between nodes
        #     group_data_structure.run()

        #     # Check if all work is complete
        #     if self.is_work_complete():
        #         break

        # # After completion, we might want to save or analyze the chat histories

if __name__ == "__main__":
    orchestrator = MainOrchestrator()
    orchestrator.run("Best Places for Vacation in India")