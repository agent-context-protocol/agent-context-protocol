import streamlit as st
import asyncio
from acp_manager import ACP
from mcp_node import MCPToolManager
import asyncio
import json
from openai import OpenAI, AsyncOpenAI
import streamlit.components.v1 as components
import json
from pathlib import Path
from collections import defaultdict
from ui_helpers import render_execution_dag

def update_and_draw_dag(data: dict, completed: set[str] | set[int], container):
    execution_list = {}
    max_depth = len(data.items())
    for sub_id, sub in data.items():
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

    execution_sequence = []
    depth = 0
    for depth in range(max_depth):
        temp = []
        for sub_id, meta_info in execution_list.items():
            
            if meta_info['depth'] == depth:
                temp.append(sub_id)
        
        if temp == []:
            break
        else:
            execution_sequence.append(temp)

    # 4. Draw
    with container:
        render_execution_dag(execution_list, completed)

st.set_page_config(layout = "wide") 
client = OpenAI()
client_async = AsyncOpenAI()
model_name = "gpt-4o-2024-08-06"
# Load custom CSS for minimal styling (removing extra background colors and padding)
def load_css():
    st.markdown("""
        <style>
        /* Grid styling */
        .grid-container {
            display: grid;
            grid-template-columns: repeat(2, 1fr); /* Two columns */
            gap: 20px;
            padding: 10px;
        }

        .grid-item {
            padding: 15px;
            background-color: #f1f1f1;
            border-radius: 8px;
            text-align: left;
            box-shadow: none;
            font-size: 16px;
            cursor: default;
        }

        /* Custom font styling */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Arial', sans-serif;
            font-weight: normal;
        }

        p {
            font-family: 'Helvetica', sans-serif;
        }

        /* Simplified progress bar styling */
        .stProgress > div > div > div > div {
            background-color: #4CAF50;
        }

        /* Minimal button styling */
        .stButton>button {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 14px;
            border-radius: 6px;
        }

        /* Scrollbar customization */
        ::-webkit-scrollbar {
            width: 10px;
        }

        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }

        ::-webkit-scrollbar-thumb {
            background: #888;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }

        /* SubTask max height with scrollable content */
        .scrollable-panel {
            width: 100%;  /* Take up 100% of the column width */
            max-height: 500px;  /* Set maximum height */
            padding: 20px;
            border: 2px solid white;
            border-radius: 10px;
            background-color: black;
            color: white;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.5);  
            overflow-y: auto;  /* Scrollable when content exceeds max height */
        }

        /* Ensure headings and paragraphs are white */
        .scrollable-panel h3, .scrollable-panel h4, .scrollable-panel p {
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)


class StreamlitACP:
    def __init__(self):
        self.mcp_manager = None
        self.ACP = None
        self.output = {}
        self.group_containers = {}
        self.subtasks = []

    async def async_init(self):
        self.mcp_manager = MCPToolManager()
        await self.mcp_manager.load_from_config("config.yml")
        self.ACP = ACP(mcp_tool_manager=self.mcp_manager)

    def create_group_sections(self, execution_blueprint):
        """
        For each group, create a full‐width container and render the stub panel.
        """

        self.dag_placeholders = {} 
        for gid, gdata in execution_blueprint.items():
            container = st.container()
            self.group_containers[gid] = container
            left_col, _ = container.columns([1, 3])  # 25% left, 75% right (blank)
            with left_col:
                update_and_draw_dag(
                    gdata,
                    completed=set(),
                    container=left_col.empty()
                )

            # with container:
            #     subtasks_html = "".join(
            #         f"<p><b>SubTask {s_id}:</b> {s['subtask_description']}</p>"
            #         for s_id, s in gdata.items()
            #     )
            #     st.markdown(f"""
            #         <div class="scrollable-panel">
            #             <h3>Group {gid}</h3>
            #             {subtasks_html}
            #         </div>
            #     """, unsafe_allow_html=True)

    def update_group_section(self, group_id, user_query):
        # gid, container = next(
        #     (g, c) for g, c in self.group_placeholders if g == group_id
        # )

        # Load system prompt
        
        with open(f"prompts/dashboard_prompt.txt", "r") as f:
            system_prompt = f.read()
        with open(f"execution_blueprint_updated_{group_id}.json", "r") as f:
            data = json.load(f)

        queries   = []                       # each sub-task’s natural-language query
        variables = defaultdict(list)        # input + output vars keyed by sub-task
        outputs   = defaultdict(list)        # output-only vars keyed by sub-task

        for sub_id, sub in data.items():
            queries.append(
                {"subtask_id": sub_id,
                "query": sub.get("subtask_description", "").strip()}
            )
            for step_id, step in sub.get("steps", {}).items():

                # input variables
                for v in step.get("input_vars", []):
                    variables[sub_id].append(
                        {"step_id": step_id,
                        "name": v["name"],
                        "value": v.get("value"),
                        "description": v.get("description"),
                        "kind": "input"}
                    ) 

                # output variables
                for v in step.get("output_vars", []):
                    rec = {"step_id": step_id,
                        "name": v["name"],
                        "value": v.get("value"),
                        "description": v.get("description"),
                        "kind": "output"}
                    variables[sub_id].append(rec)
                    outputs[sub_id].append(rec)
        input_data = f"Query: {user_query}\n"
        for sid, outlist in outputs.items():
            input_data+=f"Sub-task {sid}:\n"
            for v in outlist:
                input_data+=f" {v}\n"
        input_data = json.dumps(data, indent=2)
        # Prepare execution blueprint content
        # Prepare the prompt for the LLM
        completion = client.chat.completions.create(
                        model=model_name,
                        messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_data}
            ],
                        temperature = 0
                    ) 
        
        raw_html_snippet = completion.choices[0].message.content.split("### FORMATTED_OUTPUT")[-1].strip()
        print("Raw HTML Snippet: ", raw_html_snippet)
        full_doc = f"""
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="UTF-8"/>
          </head>
          <body style="margin:0; padding:1rem;">
            {raw_html_snippet}
          </body>
        </html>
        """
        # print(dashboard_html)
        # Render the LLM-generated dashboard
        container = self.group_containers[group_id]
        with container:
            # st.subheader(f"Group {group_id} — Completed")
            components.html(full_doc, height=1200, scrolling=True)
    async def run_acp(self, user_query, execution_blueprint):
        # Display the group subtasks
        self.create_group_sections(execution_blueprint)

        # Iterate through the groups asynchronously
        async for group_id in self.ACP.run(user_query, execution_blueprint):
            self.output[group_id] = 'group_results'
            # Update the group as completed
            self.update_group_section(group_id, user_query)

async def main():
    # Load custom CSS
    load_css()

    st.title("Execution Blueprint Executor")
    acp_app = StreamlitACP()
    await acp_app.async_init()

    # Sidebar for user input
    with st.sidebar:
        st.header("User Input")
        user_query = st.text_area("Enter your query:")
        if st.button("Example Query"):
            user_query = "Example query"

    if st.button("Run Workflow"):
        with st.spinner("Running execution_blueprint... please wait"):
            st.write("Running execution_blueprint...")
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Initialize the execution_blueprint
            execution_blueprint = await acp_app.ACP.initialise(user_query)

            async def update_progress():
                total_groups = len(acp_app.ACP.dag_compiler.execution_blueprint)
                while True:
                    completed_groups = len(acp_app.output)
                    progress = completed_groups / total_groups
                    progress_bar.progress(progress)
                    status_text.text(f"Completed {completed_groups} out of {total_groups} groups")
                    if progress >= 1.0:
                        break
                    await asyncio.sleep(0.1)

            # Run the acp and update progress simultaneously
            await asyncio.gather(
                acp_app.run_acp(user_query, execution_blueprint),
                update_progress()
            )

            st.success("ACP completed!")

if __name__ == "__main__":
    asyncio.run(main())