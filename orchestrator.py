# main_orchestrator.py
from interpreter import InterpreterNode
from main_translator import MainTranslatorNode
from local_translator import LocalTranslatorNode

class MainOrchestrator:
    def __init__(self):
        self.interpreter = InterpreterNode('interpreter')
        self.main_translator = MainTranslatorNode('main_translator')
        self.local_translators = {}

    def run(self, user_query):
        # Send user query to interpreter
        self.interpreter.user_query = user_query

        # Get initial setup from interpreter and send to main translator
        initial_setup = self.interpreter.setup()
        message = self.main_translator.setup()
        group_data_structure =  create_groups(message) 
        setup_message = group_data_structure.setup()
        confirmation = self.main_translator.communicate(setup_message)
        group_data_structure.recieve_confirmation = 

        # Main loop
        while True:
            # Process messages between nodes
            group_data_structure.run()

            # Check if all work is complete
            if self.is_work_complete():
                break

        # After completion, we might want to save or analyze the chat histories

if __name__ == "__main__":
    orchestrator = MainOrchestrator()
    orchestrator.run("Best Places for Vacation in India")