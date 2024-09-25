import asyncio
import json
from interpreter import InterpreterNode
from main_translator import MainTranslatorNode
from local_translator import LocalTranslatorNode
from concurrent.futures import ThreadPoolExecutor

class Manager:
    def __init__(self, workflow, main_translator, local_translator_system_prompt):
        self.main_translator = main_translator
        self.groups = {}
        self.local_translators = {}
        self.thread_pool = ThreadPoolExecutor()
        
        for group_id, group_data in workflow.items():
            group_translators = []
            for translator_id, translator_data in group_data.items():
                translator = LocalTranslatorNode(
                    int(translator_id),
                    translator_data["panel_description"],
                    system_prompt=local_translator_system_prompt,
                    main_translator=self.main_translator
                )
                translator.group_workflow = group_data
                translator.panel_workflow = translator_data["steps"]
                self.local_translators[translator_id] = translator
                group_translators.append(translator)
            self.groups[group_id] = group_translators
    async def run(self):
        # Start the main translator's queue processing
        main_translator_task = asyncio.create_task(self.main_translator.process_queue())

        # Run groups asynchronously (in parallel)
        group_tasks = [self.run_group_sequentially(self.groups[group_id]) for group_id in self.groups.keys()]
        await asyncio.gather(*group_tasks)
        
        # Cancel the main translator's queue processing when all groups are done
        main_translator_task.cancel()
        try:
            await main_translator_task
        except asyncio.CancelledError:
            pass

    async def run_group_sequentially(self, group):
        for translator in group:
            # Run the non-async build_verify method in a separate thread
            await asyncio.get_event_loop().run_in_executor(self.thread_pool, translator.build_verify)

    def __del__(self):
        self.thread_pool.shutdown(wait=True)

class MainOrchestrator:
    def __init__(self):
        self.get_system_prompts()
        self.interpreter = InterpreterNode('interpreter', system_prompt=self.interpreter_system_prompt)
        self.main_translator = MainTranslatorNode('main_translator', self.main_translator_system_prompt)

    def get_system_prompts(self):
        with open('prompts/interpreter_system_prompt.txt', 'r') as file:
            self.interpreter_system_prompt = file.read()

        with open('prompts/main_translator/main_translator_system_prompt.txt', 'r') as file:
            self.main_translator_system_prompt = file.read()
        
        with open('prompts/local_translator/local_translator_system_prompt.txt', 'r') as file:
            self.local_translator_system_prompt = file.read()

    async def run(self, user_query):
        # Get initial setup from interpreter and send to main translator
        self.interpreter.user_query = user_query
        panels_list = self.interpreter.setup()
        workflow = self.main_translator.setup(user_query, panels_list)
        
        # For now, we're loading the workflow from a file
        with open("workflow.json", "r") as json_file:
            workflow = json.load(json_file)

        print("Workflow:", workflow)

        communication_manager = Manager(workflow, self.main_translator, self.local_translator_system_prompt)
        await communication_manager.run()

        # Main loop
        while True:
            # Process messages between nodes
            # You might want to implement a method in Manager to handle this
            await communication_manager.process_messages()

            # Check if all work is complete
            if await self.is_work_complete():
                break

        # After completion, we might want to save or analyze the chat histories

    async def is_work_complete(self):
        # Implement logic to check if all work is complete
        # This might involve checking the state of all translators
        return False  # Placeholder

async def main():
    orchestrator = MainOrchestrator()
    # await orchestrator.run("what is the weather in seattle, usa")
    # await orchestrator.run("what is the weather in seattle, usa. Also what are the best spots to visit in seattle?")
    await orchestrator.run("tell me top 5 vacation spots in europe and current weather there")
    # await orchestrator.run("how to cook cheese burger?")

if __name__ == "__main__":
    asyncio.run(main())