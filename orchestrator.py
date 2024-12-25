import asyncio
import json
from interpreter import InterpreterNode
from main_translator import MainTranslatorNode
from local_translator import LocalTranslatorNode
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

client = OpenAI()
# client = AzureOpenAI()

# GLOBAL VARIABLE
all_panel_outputs = {}

class Manager:
    def __init__(self, workflow, file_path_str, main_translator, local_translator_system_prompt):
        self.file_path_str = file_path_str
        self.main_translator = main_translator
        self.local_translator_system_prompt = local_translator_system_prompt
        self.groups = {}
        self.local_translators = {}
        self.thread_pool = ThreadPoolExecutor()
        self.modification_count = {}  # Track modification attempts for each group
        
        for group_id, group_data in workflow.items():
            if group_id == "user_query":
                continue
            group_translators = []
            for translator_id, translator_data in group_data.items():
                translator = LocalTranslatorNode(
                    int(translator_id),
                    workflow["user_query"],
                    translator_data["panel_description"],
                    system_prompt=local_translator_system_prompt,
                    main_translator=self.main_translator,
                    file_path_str=file_path_str
                )
                translator.group_workflow = group_data
                translator.group_id = group_id
                translator.panel_workflow = translator_data["steps"]
                self.local_translators[translator_id] = translator
                group_translators.append(translator)
            self.groups[group_id] = group_translators
            self.modification_count[group_id] = 0  # Initialize modification count for each group

    # async def run(self):
    #     main_translator_task = asyncio.create_task(self.main_translator.process_queue())

    #     group_tasks = []
    #     for group_id in self.groups.keys():
    #         task = asyncio.create_task(self.run_group(group_id))
    #         group_tasks.append(task)

    #     for completed_task in asyncio.as_completed(group_tasks):
    #         group_id, group_results = await completed_task
    #         yield group_id, group_results

    #     main_translator_task.cancel()
    #     try:
    #         await main_translator_task
    #     except asyncio.CancelledError:
    #         pass

    async def run(self):
        # Start processing the main translator queue
        main_translator_task = asyncio.create_task(self.main_translator.process_queue())

        # Run each group task sequentially
        for group_id in self.groups.keys():
            group_id, group_results = await self.run_group(group_id)
            yield group_id, group_results

        # Cancel the main translator task
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
        self.modification_count[group_id] += 1  # Increment modification count
        for group_id, group_data in modified_workflow.items():
            if group_id == "user_query":
                continue
            group_translators = []
            for translator_id, translator_data in group_data.items():
                translator = LocalTranslatorNode(
                    int(translator_id),
                    modified_workflow["user_query"],
                    translator_data["panel_description"],
                    system_prompt=self.local_translator_system_prompt,
                    main_translator=self.main_translator,
                    file_path_str=self.file_path_str,
                )
                translator.group_workflow = group_data
                translator.group_id = group_id
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
                    print("\ntranslator.group_workflow : ",translator.group_workflow)
                    if self.modification_count[group_id] < 2:
                        group_done = False
                        await self.modify_group(translator.group_workflow, group_id)
                        break
                    else:
                        print(f"Dropping Translator {translator.panel_no} in group {group_id} due to excessive modifications.")
                        translator.drop = True
                        # return None
                group_results[translator.panel_no] =translator.get_results()
                all_panel_outputs[translator.panel_no] = group_results[translator.panel_no]['output']
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
        all_panel_outputs = {}
        return workflow

    async def run(self, user_query, workflow, file_path_str):
        # Get initial setup from interpreter and send to main translator
        # self.interpreter.user_query = user_query
        # panels_list = self.interpreter.setup()
        # workflow = self.main_translator.setup(user_query, panels_list)
        
        # For now, we're loading the workflow from a file
        with open("workflow.json", "r") as json_file:
            workflow = json.load(json_file)

        print("Workflow:", workflow)

        communication_manager = Manager(workflow, file_path_str, self.main_translator, self.local_translator_system_prompt)
        
        # Modify the Manager to yield results as groups complete
        async for group_id, group_results in communication_manager.run():
            yield group_id, group_results

        # In the end we accumulate details from all the panels and prepare a final answer for GAIA
        formatted_output = ""
        for step, output in all_panel_outputs.items():
            formatted_output += f"Step {step}:\n{output}\n"
        print("\nformatted_output : ",formatted_output)
        # Load the template file
        with open('prompts/GAIA_prepare_answer.txt', 'r') as file:
            prepare_GAIA_answer_system_prompt = file.read()
        # Format the final string with question and answer
        formatted_prompt = prepare_GAIA_answer_system_prompt.format(question=user_query, answer=formatted_output)
        # LLM Call to prepare final output for GAIA
        completion = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
            {"role": "user", 
            "content": formatted_prompt}
            ],
            temperature = 0
        )
        output = completion.choices[0].message.content
        # Save the string to a file
        with open('GAIA_Answer.json', 'w') as file:
            json.dump(output, file)
        print("output : ",output)
        


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