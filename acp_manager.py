import asyncio
import json
from task_decomposer import TaskDecompositionNode
from dag_compiler import DAGCompilerNode
from agent import AgentNode
from concurrent.futures import ThreadPoolExecutor

class ACPManager:
    def __init__(self, workflow, dag_compiler, agent_system_prompt):
        self.dag_compiler = dag_compiler
        self.agent_system_prompt = agent_system_prompt
        self.groups = {}
        self.agents = {}
        self.thread_pool = ThreadPoolExecutor()
        
        for group_id, group_data in workflow.items():
            group_translators = []
            for translator_id, translator_data in group_data.items():
                translator = AgentNode(
                    int(translator_id),
                    translator_data["panel_description"],
                    system_prompt=agent_system_prompt,
                    dag_compiler=self.dag_compiler
                )
                translator.group_workflow = group_data
                translator.group_id = group_id
                translator.panel_workflow = translator_data["steps"]
                self.agents[translator_id] = translator
                group_translators.append(translator)
            self.groups[group_id] = group_translators

    async def run(self):
        dag_compiler_task = asyncio.create_task(self.dag_compiler.process_queue())

        group_tasks = []
        for group_id in self.groups.keys():
            task = asyncio.create_task(self.run_group(group_id))
            group_tasks.append(task)

        for completed_task in asyncio.as_completed(group_tasks):
            group_id, group_results = await completed_task
            yield group_id, group_results

        dag_compiler_task.cancel()
        try:
            await dag_compiler_task
        except asyncio.CancelledError:
            pass

    async def modify_group(self, modified_workflow, group_id):
        for group_id, group_data in modified_workflow.items():
            group_translators = []
            for translator_id, translator_data in group_data.items():
                translator = AgentNode(
                    int(translator_id),
                    translator_data["panel_description"],
                    system_prompt=self.agent_system_prompt,
                    dag_compiler=self.dag_compiler
                )
                translator.group_workflow = group_data
                translator.group_id = group_id
                translator.panel_workflow = translator_data["steps"]
                self.agents[translator_id] = translator
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
                    group_done = False
                    await self.modify_group(translator.group_workflow, group_id)
                    break
                        # return None
                group_results[translator.panel_no] = translator.get_results()
                # except Exception as e:
                #     print(f"Error in translator {translator.panel_no}: {str(e)}")

            counter += 1
            if group_done:
                break 

        return group_id, group_results

    def __del__(self):
        self.thread_pool.shutdown(wait=True)

class ACPOrchestrator:
    def __init__(self):
        self.get_system_prompts()
        self.task_decomposer = TaskDecompositionNode('task_decomposer', system_prompt=self.task_decomposer_system_prompt)
        self.dag_compiler = DAGCompilerNode('dag_compiler', self.dag_compiler_system_prompt)

    def get_system_prompts(self):
        with open('prompts/task_decomposer_system_prompt.txt', 'r') as file:
            self.task_decomposer_system_prompt = file.read()

        with open('prompts/dag_compiler/dag_compiler_system_prompt.txt', 'r') as file:
            self.dag_compiler_system_prompt = file.read()
        
        with open('prompts/agent/agent_system_prompt.txt', 'r') as file:
            self.agent_system_prompt = file.read()

    async def initialise(self, user_query):
        self.task_decomposer.user_query = user_query
        panels_list = self.task_decomposer.setup()
        workflow = self.dag_compiler.setup(user_query, panels_list)
        return workflow

    async def run(self, user_query, workflow):
        # Get initial setup from task_decomposer and send to main translator
        # self.task_decomposer.user_query = user_query
        # panels_list = self.task_decomposer.setup()
        # workflow = self.dag_compiler.setup(user_query, panels_list)
        
        # For now, we're loading the workflow from a file
        with open("workflow.json", "r") as json_file:
            workflow = json.load(json_file)

        print("Workflow:", workflow)

        communication_manager = ACPManager(workflow, self.dag_compiler, self.agent_system_prompt)
        
        # Modify the Manager to yield results as groups complete
        # await communication_manager.run()
        async for group_id, group_results in communication_manager.run():
            yield group_id, group_results



async def main():
    orchestrator = ACPOrchestrator()
    await orchestrator.run("what is the weather in seattle, usa", '')

if __name__ == "__main__":
    asyncio.run(main())