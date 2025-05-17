import asyncio
import json
from .task_decomposer import TaskDecompositionNode
from .dag_compiler import DAGCompilerNode
from .agent import AgentNode
from concurrent.futures import ThreadPoolExecutor
from importlib import resources
import agent_context_protocol.prompts as root_prompts
import agent_context_protocol.prompts.agent as agent_prompts
import agent_context_protocol.prompts.dag_compiler as dag_compiler_prompts

class ACPManager:
    def __init__(self, execution_blueprint, dag_compiler, agent_system_prompt):
        self.dag_compiler = dag_compiler
        self.agent_system_prompt = agent_system_prompt
        self.groups = {}
        self.agents = {}
        self.thread_pool = ThreadPoolExecutor()
        self.completed_agents = []
        for group_id, group_data in execution_blueprint.items():            
            execution_list = {}
            max_depth = len(group_data.items())
            for sub_id, sub in group_data.items():
                execution_list[sub_id] = {
                    'dependent_on' : [],
                    'depth' : 0
                }
                for step in sub["steps"].values():
                    for inp in step["input_vars"]:
                        for dep in inp.get("dependencies", []):
                            if dep['sub_task'] not in execution_list[sub_id]['dependent_on']:
                                execution_list[sub_id]['dependent_on'].append(dep['sub_task'])
            for sub_id, meta_info in execution_list.items():
                for parent_node in meta_info['dependent_on']:
                    if meta_info['depth'] <= execution_list[str(parent_node)]['depth']:
                        meta_info['depth'] = execution_list[str(parent_node)]['depth'] + 1
            for agent_id, agent_data in group_data.items():
                agent = AgentNode(
                    int(agent_id),
                    agent_data["subtask_description"],
                    system_prompt=agent_system_prompt,
                    dag_compiler=self.dag_compiler
                )
                agent.group_execution_blueprint = group_data
                agent.group_id = group_id
                agent.sub_task_execution_blueprint = agent_data["steps"]
                self.agents[agent_id] = agent
            execution_sequence = []
            depth = 0
            for depth in range(max_depth):
                temp = []
                for sub_id, meta_info in execution_list.items():
                    
                    if meta_info['depth'] == depth:
                        temp.append(self.agents[sub_id])
                
                if temp == []:
                    break
                else:
                    execution_sequence.append(temp)
            print(execution_sequence)
            self.groups[group_id] = execution_sequence

    async def run(self):
        dag_compiler_task = asyncio.create_task(self.dag_compiler.process_queue())

        group_tasks = []
        for group_id in self.groups.keys():
            task = asyncio.create_task(self.run_group(group_id))
            group_tasks.append(task)

        for completed_task in asyncio.as_completed(group_tasks):
            group_id = await completed_task
            yield group_id

        dag_compiler_task.cancel()
        try:
            await dag_compiler_task
        except asyncio.CancelledError:
            pass

    async def modify_group(self, modified_execution_blueprint, group_id):
        for group_id, group_data in modified_execution_blueprint.items():
            execution_list = {}
            max_depth = len(group_data.items())
            for sub_id, sub in group_data.items():
                execution_list[sub_id] = {
                    'dependent_on' : [],
                    'depth' : 0
                }
                for step in sub["steps"].values():
                    for inp in step["input_vars"]:
                        for dep in inp.get("dependencies", []):
                            if dep['sub_task'] not in execution_list[sub_id]['dependent_on']:
                                execution_list[sub_id]['dependent_on'].append(dep['sub_task'])
            for sub_id, meta_info in execution_list.items():
                
                    # print(sub_id)
                for parent_node in meta_info['dependent_on']:
                    if meta_info['depth'] <= execution_list[str(parent_node)]['depth']:
                        meta_info['depth'] = execution_list[str(parent_node)]['depth'] + 1
            
            for agent_id, agent_data in group_data.items():
                agent = AgentNode(
                    int(agent_id),
                    agent_data["subtask_description"],
                    system_prompt=self.agent_system_prompt,
                    dag_compiler=self.dag_compiler
                )
                agent.group_execution_blueprint = group_data
                agent.group_id = group_id
                agent.sub_task_execution_blueprint = agent_data["steps"]
                self.agents[agent_id] = agent
            execution_sequence = []
            depth = 0
            for depth in range(max_depth):
                temp = []
                for sub_id, meta_info in execution_list.items():
                    
                    if meta_info['depth'] == depth and sub_id not in self.completed_agents:
                        temp.append(self.agents[sub_id])
                
                if temp == []:
                    break
                else:
                    execution_sequence.append(temp)
            # group_agents.append(agent)
            self.groups[group_id] = execution_sequence
            print(execution_sequence)

        print('Successfully Modified This Groups execution_blueprint.')

        await asyncio.sleep(0.1)

    async def run_agent(self, agent, group_id):
        group_done = True
        await agent.build_verify()
        if agent.drop:
            print('Dropping This execution_blueprint...')
            agent.drop = False
                    
        if agent.modify:
            print('Modifying This execution_blueprint...')
            print("\nagent.group_execution_blueprint : ",agent.group_execution_blueprint)
            group_done = False
            await self.modify_group(agent.group_execution_blueprint, group_id)
            agent.modify = False
        res = agent.get_results() 
        return group_done, agent.sub_task_no       

    async def run_group(self, group_id):
        
        group_done = False
        counter = 0
        while True and counter < 5:
            group_done = True
            # group_done = True
            print(f"\n#################\nTrial Attempt {counter}")
            for agents in self.groups[group_id]:
                agent_tasks = [
                    asyncio.create_task(self.run_agent(agent, group_id))
                    for agent in agents
                ] 
                # wait for _all_ of them to finish
                results = await asyncio.gather(*agent_tasks, return_exceptions=False)

                # process the batch’s results
                batch_done = True
                for group_done_flag, agent_id in results:
                    if group_done_flag:
                        self.completed_agents.append(agent_id)
                    else:
                        batch_done = False
                        
                if not batch_done:
                    group_done = False
                    break

            counter += 1
            if group_done:
                break 

        return group_id

    def __del__(self):
        self.thread_pool.shutdown(wait=True)

class ACP:
    def __init__(self, mcp_tool_manager):
        self.mcp_tool_manager = mcp_tool_manager
        self.get_system_prompts()
        self.task_decomposer = TaskDecompositionNode('task_decomposer', system_prompt=self.task_decomposer_system_prompt, mcp_tool_manager=self.mcp_tool_manager)
        self.dag_compiler = DAGCompilerNode('dag_compiler', self.dag_compiler_system_prompt, mcp_tool_manager=self.mcp_tool_manager)
        self.communication_manager = None

    def get_system_prompts(self):
        with resources.open_text(root_prompts, "task_decomposer_system_prompt.txt") as file:
            self.task_decomposer_system_prompt = file.read()

        with resources.open_text(dag_compiler_prompts, "dag_compiler_system_prompt.txt") as file:
            self.dag_compiler_system_prompt = file.read()

        with resources.open_text(agent_prompts, "agent_system_prompt.txt") as file:
            self.agent_system_prompt = file.read()

    async def initialise(self, user_query):
        self.task_decomposer.user_query = user_query
        subtask_list = self.task_decomposer.setup()
        execution_blueprint = self.dag_compiler.setup(user_query, subtask_list)
        return execution_blueprint

    async def run(self, user_query, execution_blueprint):
        # Get initial setup from task_decomposer and send to dag compiler
       
        # For now, we're loading the execution_blueprint from a file
        with open("execution_blueprint.json", "r") as json_file:
            execution_blueprint = json.load(json_file)

        print("execution_blueprint:", execution_blueprint)

        self.communication_manager = ACPManager(execution_blueprint, self.dag_compiler, self.agent_system_prompt)
        async for group_id in self.communication_manager.run():
            yield group_id



async def main():
    config_path = "config.yml"
    # manager = MCPToolManager()
    # await manager.load_from_config(config_path)
    # acp = ACP(mcp_tool_manager=manager)
    # # await acp.run("what is the weather in seattle, usa", '')
    # user_query = "what is the weather in seattle, usa? Tell time to go from starbucks roastery till Microsoft redmond office?"
    # # user_query = "Geocode the address '1600 Amphitheatre Parkway, Mountain View, CA"
    # execution_blueprint = await acp.initialise(user_query)
    # async for group_id in acp.run(user_query, execution_blueprint):
    #     print(f"\n\nGroupID: {group_id}:\n{group_results}") 

if __name__ == "__main__":
    asyncio.run(main())