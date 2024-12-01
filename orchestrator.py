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
from utils import create_pdf_from_html

# Load environment variables from .env file
load_dotenv()

client = OpenAI()
# client = AzureOpenAI()

# GLOBAL VARIABLE
all_panel_outputs = {}

class Manager:
    def __init__(self, workflow, main_translator, local_translator_system_prompt):
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
                    main_translator=self.main_translator
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
                    main_translator=self.main_translator
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
                all_panel_outputs[translator.panel_no] = translator.get_results()['output']
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
        print("panels_listtttttt : ",panels_list)
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

        # In the end we accumulate details from all the panels and prepare a final answer for GAIA
        formatted_output = ""
        sorted_all_panel_outputs = dict(sorted(all_panel_outputs.items()))
        for step, output in sorted_all_panel_outputs.items():
            formatted_output += f"Step {step}:\n{output}\n"
        print("\nformatted_output : ",formatted_output)
        # Load the template file
        with open('prompts/final_report_formatting.txt', 'r') as file:
            final_report_formatting_system_prompt = file.read()

        report_so_far_main = ""
        report_so_far_ref = "\n<h2>References</h2>"
        section_details = self.main_translator.panel_details
        # for pidx, panel_out in enumerate(formatted_output):
        for pidx, panel_out in sorted_all_panel_outputs.items():
            # report_iter += 1
            frm_prmpt = final_report_formatting_system_prompt.format(user_query=user_query, panel_steps=panel_out, panel_idx=pidx, report_so_far=report_so_far_main + report_so_far_ref, section_details=section_details)
            print("frm_prmpt : ",frm_prmpt)
            completion = client.chat.completions.create(
                    model="gpt-4o-2024-08-06",
                    messages=[
                        {"role": "user", 
                        "content": frm_prmpt}
                        ],
                    temperature = 0
                )

            output = completion.choices[0].message.content
            output = output.replace("```html", "").replace("```", "")
            print("\noutput : ",output)
            if "$$TERMINATE$$" in output:
                break
            elif "$$REPORT_SECTION" in output:
                report_part = output.split("$$REPORT_SECTION$$")[1].split("$$REFERENCES$$")
                report_part_main = report_part[0]
                references = report_part[1]
                report_so_far_main = report_so_far_main + "\n" + report_part_main
                report_so_far_ref = report_so_far_ref + "\n" + references
                # print("\nreport_so_far : ",report_so_far_main + report_so_far_ref)

        # Save the string to a pdf file
        create_pdf_from_html(report_so_far_main + report_so_far_ref, "generated_report.pdf")
        print("output : ",report_so_far_main + report_so_far_ref) 
        


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