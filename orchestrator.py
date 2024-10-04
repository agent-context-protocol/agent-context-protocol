import asyncio
import json
from interpreter import InterpreterNode
from main_translator import MainTranslatorNode
from local_translator import LocalTranslatorNode
from concurrent.futures import ThreadPoolExecutor

class Manager:
    def __init__(self, workflow, main_translator, local_translator_system_prompt):
        self.main_translator = main_translator
        self.local_translator_system_prompt = local_translator_system_prompt
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
        main_translator_task = asyncio.create_task(self.main_translator.process_queue())

        group_tasks = []
        for group_id in self.groups.keys():
            task = asyncio.create_task(self.run_group(group_id))
            group_tasks.append(task)

        for completed_task in asyncio.as_completed(group_tasks):
            group_id, group_results = await completed_task
            yield group_id, group_results

        main_translator_task.cancel()
        try:
            await main_translator_task
        except asyncio.CancelledError:
            pass

    async def modify_group(self, modified_workflow, group_id):
        # group_translators = []
        # print(modified_workflow)
        # for translator_id, translator_data in modified_workflow.items():
        #     translator = LocalTranslatorNode(
        #         int(translator_id),
        #         translator_data["panel_description"],
        #         system_prompt=local_translator_system_prompt,
        #         main_translator=self.main_translator
        #     )
        #     translator.group_workflow = group_data
        #     translator.panel_workflow = translator_data["steps"]
        #     self.local_translators[translator_id] = translator
        #     group_translators.append(translator)
        # self.groups[group_id] = group_translators
        for group_id, group_data in modified_workflow.items():
            group_translators = []
            for translator_id, translator_data in group_data.items():
                translator = LocalTranslatorNode(
                    int(translator_id),
                    translator_data["panel_description"],
                    system_prompt=self.local_translator_system_prompt,
                    main_translator=self.main_translator
                )
                translator.group_workflow = group_data
                translator.panel_workflow = translator_data["steps"]
                self.local_translators[translator_id] = translator
                group_translators.append(translator)
            self.groups[group_id] = group_translators

        print('Successfully Modified This Groups Workflow.')

        await asyncio.sleep(0.1)

    async def run_group(self, group_id):
        group_results = {}
        group_done = False
        counter = 0
        while True and counter < 5:
            group_done = True
            for translator in self.groups[group_id]:
                # try:
                await translator.build_verify()
                if translator.drop:
                    print('Dropping This Workflow...')
                    
                if translator.modify:
                    print('Modifying This Workflow...')
                    group_done = False
                    await self.modify_group(translator.group_workflow, group_id)
                    break
                        # return None
                group_results[translator.panel_no] =translator.get_results()
                # except Exception as e:
                #     print(f"Error in translator {translator.panel_no}: {str(e)}")

            counter += 1
            if group_done:
                break 

        return group_id, group_results

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

    async def initialise(self, user_query):
        self.interpreter.user_query = user_query
        panels_list = self.interpreter.setup()
        workflow = self.main_translator.setup(user_query, panels_list)
        return workflow

    async def run(self, user_query, workflow):
        # Get initial setup from interpreter and send to main translator
        # self.interpreter.user_query = user_query
        # panels_list = self.interpreter.setup()
        # workflow = self.main_translator.setup(user_query, panels_list)
        
        # For now, we're loading the workflow from a file
        with open("workflow.json", "r") as json_file:
            workflow = json.load(json_file)

        print("Workflow:", workflow)

        communication_manager = Manager(workflow, self.main_translator, self.local_translator_system_prompt)
        
        # Modify the Manager to yield results as groups complete
        async for group_id, group_results in communication_manager.run():
            yield group_id, group_results



async def main():
    orchestrator = MainOrchestrator()
    await orchestrator.run("what is the weather in seattle, usa")
    # await orchestrator.run("what is the weather in seattle, usa. Also what are the best spots to visit in seattle?")
    # await orchestrator.run("tell me top 30 vacation spots in europe and current weather there no illustrations")
    # await orchestrator.run("What are the top 5 most rainy areas in the world?.")
    # await orchestrator.run("what are top news headlines for today? What is the weather at some of the top news headline locations")
    # await orchestrator.run("where in the world should i go for travelling? What is the weather and current news at those places? Also i want to understand what generally causes null pointer errors in java")


if __name__ == "__main__":
    asyncio.run(main())