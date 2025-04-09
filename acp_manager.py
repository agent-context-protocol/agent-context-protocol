import asyncio
import json
from task_decomposer import TaskDecompositionNode
from dag_compiler import DAGCompilerNode
from agent import AgentNode
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
from utils import create_pdf_from_html, create_pdf_from_latex
import re
from together import Together
from base import save_metrics_to_json, BaseNode
import datetime

# Load environment variables from .env file
load_dotenv()

client = OpenAI()
# client = AzureOpenAI()
# client = Together()

# Model options:
# o1-2024-12-17
# deepseek-ai/DeepSeek-R1
model_name = "o1-2024-12-17"


# GLOBAL VARIABLE
all_subtask_outputs = {}

class ACPManager:
    def __init__(self, execution_blueprint, dag_compiler, agent_system_prompt):
        self.dag_compiler = dag_compiler
        self.agent_system_prompt = agent_system_prompt
        self.groups = {}
        self.agents = {}
        self.thread_pool = ThreadPoolExecutor()
        self.modification_count = {}  # Track modification attempts for each group
        self.user_query = execution_blueprint["user_query"]
        
        for group_id, group_data in execution_blueprint.items():
            if group_id == "user_query":
                continue
            group_agents = []
            for agent_id, agent_data in group_data.items():
                agent = AgentNode(
                    int(agent_id),
                    execution_blueprint["user_query"],
                    agent_data["subtask_description"],
                    system_prompt=agent_system_prompt,
                    dag_compiler=self.dag_compiler
                )
                agent.group_execution_blueprint = group_data
                agent.group_id = group_id
                agent.sub_task_execution_blueprint = agent_data["steps"]
                self.agents[agent_id] = agent
                group_agents.append(agent)
            self.groups[group_id] = group_agents
            self.modification_count[group_id] = 0  # Initialize modification count for each group

    # async def run(self):
    #     dag_compiler_task = asyncio.create_task(self.dag_compiler.process_queue())

    #     group_tasks = []
    #     for group_id in self.groups.keys():
    #         task = asyncio.create_task(self.run_group(group_id))
    #         group_tasks.append(task)

    #     for completed_task in asyncio.as_completed(group_tasks):
    #         group_id, group_results = await completed_task
    #         yield group_id, group_results

    #     dag_compiler_task.cancel()
    #     try:
    #         await dag_compiler_task
    #     except asyncio.CancelledError:
    #         pass

    async def run(self):
        # Start processing the main agent queue
        dag_compiler_task = asyncio.create_task(self.dag_compiler.process_queue())

        # Run each group task sequentially
        for group_id in self.groups.keys():
            group_id, group_results = await self.run_group(group_id)
            yield group_id, group_results

        # Cancel the main agent task
        dag_compiler_task.cancel()
        try:
            await dag_compiler_task
        except asyncio.CancelledError:
            pass

    async def modify_group(self, modified_execution_blueprint, group_id):
        # group_agents = []
        # print(modified_execution_blueprint)
        # for agent_id, agent_data in modified_execution_blueprint.items():
        #     agent = AgentNode(
        #         int(agent_id),
        #         agent_data["subtask_description"],
        #         system_prompt=agent_system_prompt,
        #         dag_compiler=self.dag_compiler
        #     )
        #     agent.group_execution_blueprint = group_data
        #     agent.sub_task_execution_blueprint = agent_data["steps"]
        #     self.agents[agent_id] = agent
        #     group_agents.append(agent)
        # self.groups[group_id] = group_agents
        self.modification_count[group_id] += 1  # Increment modification count
        for group_id, group_data in modified_execution_blueprint.items():
            if group_id == "user_query":
                continue
            group_agents = []
            for agent_id, agent_data in group_data.items():
                agent = AgentNode(
                    int(agent_id),
                    modified_execution_blueprint["user_query"],
                    agent_data["subtask_description"],
                    system_prompt=self.agent_system_prompt,
                    dag_compiler=self.dag_compiler
                )
                agent.group_execution_blueprint = group_data
                agent.group_id = group_id
                agent.sub_task_execution_blueprint = agent_data["steps"]
                self.agents[agent_id] = agent
                group_agents.append(agent)
            self.groups[group_id] = group_agents

        print('Successfully Modified This Groups execution_blueprint.')

        await asyncio.sleep(0.1)

    async def run_group(self, group_id):
        group_results = {}
        group_done = False
        counter = 0
        # Report related variables intialized
        prev_summary = f"This is additional context and not your main query. You are writing a detailed report on the topic: {self.user_query}.\nSummary from the previous sub-sections and sections of the report we are building, try to look at these summaries carefully and not search for similar things since we do not want repetitive information in the final report"
        prev_search_queries = []
        prev_img_links = []
        prev_summary_viz_tab = f"This is additional context and not your main query. You are looking for data for detailed report on the topic: {self.user_query}.\nSummary for the tables/visualization from the previous sub-sections and sections of the report we are building, try to look at these summaries carefully and not search for similar things since we do not want repetitive information in the final report"
        while True and counter < 5:
            group_done = True
            for agent in self.groups[group_id]:
                print("start forloop orch --> prev_img_links: ",prev_img_links)
                # try:
                # if prev_summary != "":
                # Report related variables
                agent.prev_summary = prev_summary + f"\n Summary for section {agent.sub_task_no}:\n"
                agent.prev_summary_viz_tab = prev_summary_viz_tab + f"\nTables/Viz Summary for section {agent.sub_task_no}:\n"
                agent.prev_sections_summary = agent.prev_summary
                agent.prev_search_queries = prev_search_queries
                agent.prev_img_links = prev_img_links
                await agent.build_verify()
                if agent.drop:
                    print('Dropping This execution_blueprint...')
                    
                if agent.modify:
                    print('Modifying This execution_blueprint...')
                    print("\nagent.group_execution_blueprint : ",agent.group_execution_blueprint)
                    if self.modification_count[group_id] < 2:
                        group_done = False
                        await self.modify_group(agent.group_execution_blueprint, group_id)
                        break
                    else:
                        print(f"Dropping agent {agent.sub_task_no} in group {group_id} due to excessive modifications.")
                        agent.drop = True
                        # return None
                group_results[agent.sub_task_no] = await agent.get_results()
                all_subtask_outputs[agent.sub_task_no] = group_results[agent.sub_task_no]['output']
                # Report related variables updated
                prev_summary = agent.prev_summary
                prev_sections_summary = agent.prev_sections_summary
                prev_search_queries = agent.prev_search_queries
                prev_img_links = agent.prev_img_links
                print("after forloop orch --> prev_img_links: ",prev_img_links)
                # except Exception as e:
                #     print(f"Error in agent {agent.sub_task_no}: {str(e)}")

            counter += 1
            if group_done:
                break 

        return group_id, group_results

    def __del__(self):
        self.thread_pool.shutdown(wait=True)

class ACP:
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
        subtask_list = self.task_decomposer.setup()
        print("subtask_list : ",subtask_list)
        execution_blueprint = self.dag_compiler.setup(user_query, subtask_list)
        return execution_blueprint

    async def run(self, user_query, execution_blueprint):
        # Get initial setup from task_decomposer and send to main agent 
        # For now, we're loading the execution_blueprint from a file
        with open("execution_blueprint.json", "r") as json_file:
            execution_blueprint = json.load(json_file)

        print("execution_blueprint:", execution_blueprint)

        communication_manager = ACPManager(execution_blueprint, self.dag_compiler, self.agent_system_prompt)
        
        # Modify the Manager to yield results as groups complete
        async for group_id, group_results in communication_manager.run():
            yield group_id, group_results



        #####################################################
        # Final Coordination Layer
        # In the end we accumulate details from all the agents and prepare a final report
        now = datetime.datetime.utcnow().isoformat()
        event = {
            "timestamp": now + "Z",  # E.g. "2025-03-24T14:55:00.123456Z"
            "description": "AccumulatorTool"
        }
        BaseNode.events.append(event)
        formatted_output = ""
        sorted_all_subtask_outputs = dict(sorted(all_subtask_outputs.items()))
        # Get the maximum key to calculate n+1
        last_key = max(sorted_all_subtask_outputs.keys())
        # Add the new entry
        sorted_all_subtask_outputs[last_key + 1] = "Conclusion:"

        with open("sorted_all_subtask_outputs_dict.json", "w") as f:
            json.dump(sorted_all_subtask_outputs, f, indent=2)
        
        for step, output in sorted_all_subtask_outputs.items():
            formatted_output += f"Step {step}:\n{output}\n"
        print("\nformatted_output : ",formatted_output)
        # Load the template file
        with open('prompts/final_report_formatting.txt', 'r') as file:
            final_report_formatting_system_prompt = file.read()
        with open('prompts/final_report_formatting_input.txt', 'r') as file:
            final_report_formatting_input_system_prompt = file.read()

        report_so_far_main = ""
        report_so_far_ref = "\n" + r"\section{References}"
        section_details = self.dag_compiler.subtask_details
        # for aidx, agent_out in enumerate(formatted_output):
        cntr_idx = 0
        section_title_set = set()
        for aidx, agent_out in sorted_all_subtask_outputs.items():
            run_final_format_success = False
            counter_final_format = 0
            error_message = ""
            while not run_final_format_success and counter_final_format < 5:
                try:
                    # report_iter += 1
                    counter_final_format += 1
                    cntr_idx += 1
                    if cntr_idx == 1:
                        frm_prmpt = final_report_formatting_system_prompt + '\nThis is the first step. Include the latex preambles and begin document like in the examples provided. Your output for the current step should have $$CHAIN_OF_THOUGHT$$, $$REPORT_SECTION$$, and $$REFERENCES$$ sections.\n' +final_report_formatting_input_system_prompt.format(user_query=user_query, step_no=agent_out, step_idx=aidx, report_so_far=report_so_far_main + report_so_far_ref, error_message=error_message)
                    else:
                        frm_prmpt = final_report_formatting_system_prompt + '\nThis is step {aidx}, and you need to look at the provided steps output details to come up with your ouptut. Do not hallucinate the output content and adhere to the step {aidx} output details provided. Since this is not the first step, so do not repeat the things like latex preambles and begin document like in the examples provided. Your output for the current step should have $$CHAIN_OF_THOUGHT$$, $$REPORT_SECTION$$, and $$REFERENCES$$ sections.\n' +final_report_formatting_input_system_prompt.format(user_query=user_query, step_no=agent_out, step_idx=aidx, report_so_far=report_so_far_main + report_so_far_ref, error_message=error_message)
                    print("frm_prmpt : ",frm_prmpt)
                    completion = client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "user", 
                                "content": frm_prmpt}
                                ],
                            # temperature = 0
                        )

                    if 'deepseek' in model_name:
                        output = completion.choices[0].message.content.split(r'</think>')[-1]
                    else:
                        output = completion.choices[0].message.content
                    output = output.replace("```latex", "").replace("```", "")
                    # output = output.replace("```", "")
                    print("\noutput : ",output)

                    ##################
                    # Checking if the format is wrong
                    chain_count = output.count("$$CHAIN_OF_THOUGHT$$") + output.count("%%%% START CHAIN_OF_THOUGHT")
                    report_count = output.count("$$REPORT_SECTION$$") + output.count("%%%% START REPORT_SECTION")
                    references_count = output.count("$$REFERENCES$$")

                    if chain_count != 2 or report_count != 2: # or references_count != 1:
                    # if chain_count == 0 or report_count == 0 or references_count == 0:
                        raise ValueError("There is either more than one occurence or no occurence of the phrases: $$CHAIN_OF_THOUGHT$$, $$REPORT_SECTION$$, $$REFERENCES$$. Each output of yours should be made up of these blocks, and they should appear only once at the start of these blocks and not repeated again.")
                    ##################

                    # report_part = output.split("$$REPORT_SECTION$$")[-1].split("$$REFERENCES$$")
                    # report_part_main = report_part[0]
                    # references = report_part[1]
                    output = output.strip()
                    report_part_main = output.split("%%%% START REPORT_SECTION")[-1]
                    report_part_main = report_part_main.split("$$REPORT_SECTION$$")[-1]
                    report_part_main = report_part_main.split("%%%% START REFERENCES")[0].strip()
                    report_part_main = report_part_main.split(r"\subsection{References}")[0].split(r"\subsection*{References}")[0].replace(r"./","")
                    pattern = r'\\section\s*\{([^}]+)\}'
                    match = re.search(pattern, report_part_main)
                    if match:
                        section_title = match.group(1) 
                        if section_title in section_title_set:
                            break

                    references = output.split("%%%% START REFERENCES")[-1]
                    references = references.split("$$REFERENCES$$")[-1].strip()

                    ####################
                    # Check to catch latex errors
                    report_so_far_main_temp = report_so_far_main + "\n" + report_part_main
                    report_so_far_ref_temp = report_so_far_ref + "\n" + references
                    report_so_far_main_temp = report_so_far_main_temp.replace(r"\end{document}", "").replace(r"./","").replace(r"\end*{document}", "")
                    report_so_far_ref_temp = report_so_far_ref_temp.replace(r"\end{document}", "").replace(r"./","").replace(r"\end*{document}", "")
                    output_till_now = report_so_far_main_temp + report_so_far_ref_temp + "\n" + r"\end{document}"
                    latex_run_bool, latex_error_message = create_pdf_from_latex(output_till_now, "save_reports/generated_report_syntax_check.pdf", True)
                    if not (latex_run_bool or "Output written on save_reports/temp_latex_file.pdf" in latex_error_message):
                        raise ValueError(latex_error_message)
                    ####################

                    report_so_far_main = report_so_far_main + "\n" + report_part_main
                    report_so_far_ref = report_so_far_ref + "\n" + references
                    # print("\nreport_so_far : ",report_so_far_main + report_so_far_ref)
                    run_final_format_success = True
                    if match:
                        section_title_set.add(section_title)
                except Exception as e:
                    cntr_idx -= 1
                    error_message = f"Please provide the correct whole output, and not just the corrected part. And avoid any internal comments or reasoning inside the blocks. In case the error is due to some image file not being found or being corrupted, lets just remove the image from the report and not use it to avoid the error.\n\nError:{str(e)}"
                    continue

            if not run_final_format_success:
                raise ValueError("Latex formatting failed")

        # Save the string to a pdf file
        # create_pdf_from_html(report_so_far_main + report_so_far_ref, "generated_report.pdf")
        report_so_far_main = report_so_far_main.replace(r"\end{document}", "")
        report_so_far_ref = report_so_far_ref.replace(r"\end{document}", "")
        final_output = report_so_far_main + report_so_far_ref + "\n" + r"\end{document}"
        latex_run_bool, latex_error_message = create_pdf_from_latex(final_output, "save_reports/generated_report.pdf")
        print("output : ",final_output) 
        print("latex_run_bool : ",latex_run_bool)
        print("latex_error_message : ",latex_error_message)

        save_metrics_to_json(cntr_idx)
        


async def main():
    acp = ACP()

if __name__ == "__main__":
    asyncio.run(main())