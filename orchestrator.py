import asyncio
from interpreter import InterpreterNode
from main_translator import MainTranslatorNode
from local_translator import LocalTranslatorNode
import json

# class Manager:
#     def __init__(self, workflow, main_translator):
#         # self.queue = asyncio.Queue()
#         # self.lock = asyncio.Lock()
#         self.groups = {}
#         self.translator_list = []
#         for group_id in sorted(workflow.keys()):
#             self.groups[group_id] = {}
#             for instance_id in sorted(workflow[group_id].keys()):
#                 self.groups[group_id][instance_id] = LocalTranslatorNode(instance_id, workflow[group_id][instance_id])
#                 self.translator_list.append(self.groups[group_id][instance_id])
#         self.main_translator = main_translator

#     async def setup_individually(self, local_translator):
#         setup_message = await local_translator.setup()
#         response = await self.query_main_translator(setup_message)
#         return response

#     async def setup(self):
#         await asyncio.gather(*(self.setup_individually(local_translator) for local_translator in self.translator_list))

#     async def query_main_translator(self, query):
#         async with self.main_translator.lock
#             response = await self.main_translator.query(query)
#             return response

#     async def run_group_sequentially(self, group): 
#         for translator in group:
#             await self.run_translator(translator)


class MainOrchestrator:
    def __init__(self):
        self.get_system_prompts()
        self.interpreter = InterpreterNode('interpreter', system_prompt = self.interpreter_system_prompt)
        self.main_translator = MainTranslatorNode('main_translator', self.main_translator_system_prompt)
        self.local_translators = {}

    def get_system_prompts(self):
        # Interpreter system prompt
        with open('prompts/interpreter_system_prompt.txt', 'r') as file:
            self.interpreter_system_prompt = file.read()

        # Main Translator System Prompt
        with open('prompts/main_translator/main_translator_system_prompt.txt', 'r') as file:
            self.main_translator_system_prompt = file.read()
        
        # Local Translator System Prompt
        with open('prompts/local_translator/local_translator_system_prompt.txt', 'r') as file:
            self.local_translator_system_prompt = file.read()

    def run(self, user_query):
        # Send user query to interpreter
        self.interpreter.user_query = user_query

        # Get initial setup from interpreter and send to main translator
        panels_list = self.interpreter.setup()
        print("panels_list : ",panels_list)
        # panels_list = []
        message = self.main_translator.setup(user_query, panels_list) 
        # with open("workflow.json", "r") as json_file:
        #     message = json.load(json_file)
        # self.local_translators_1 = LocalTranslatorNode(0, message["1"]["1"]["panel_description"], system_prompt = self.local_translator_system_prompt)
        # self.local_translators_1.workflow = message["1"]["1"]["steps"]
        # self.local_translators_1.build_verify()

        # communication_manager = Manager(workflow)
        # setup_message = group_data_structure.setup()
        # confirmation = self.main_translator.communicate(setup_message)
        # # group_data_structure.recieve_confirmation = 

        # # Main loop
        # while True:
        #     # Process messages between nodes
        #     group_data_structure.run()

        #     # Check if all work is complete
        #     if self.is_work_complete():
        #         break

        # # After completion, we might want to save or analyze the chat histories

if __name__ == "__main__":
    from google_auth_oauthlib.flow import InstalledAppFlow

    orchestrator = MainOrchestrator()
    orchestrator.run("what is segmentation fault in c++?")
