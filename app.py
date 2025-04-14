import streamlit as st
import asyncio
from acp_manager import ACP
from mcp_node import MCPToolManager
import asyncio

st.set_page_config(layout = "wide") 


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
        self.group_placeholders = {}
        self.subtasks = []

    async def async_init(self):
        self.mcp_manager = MCPToolManager()
        await self.mcp_manager.load_from_config("config.yml")
        self.ACP = ACP(mcp_tool_manager=self.mcp_manager)

    def create_group_sections(self, execution_blueprint):
        subtasks = []

        for group_id in execution_blueprint.keys():
            for subtask_id in execution_blueprint[group_id].keys():
                subtasks.append({
                    'group_id' : group_id,
                    'subtask_id' : subtask_id,
                    'subtask_description' : execution_blueprint[group_id][subtask_id]['subtask_description']}
                )

        grid = []
        for i in range(len(subtasks)//2 + 1):
            cols = st.columns(2)  # Fixed 2 columns per row
            grid_row = []
            
            for j in range(2):
                container = cols[j].empty()  # Create an empty container for each column
                grid_row.append(container)
            grid.append(grid_row)

        self.group_placeholders = grid
        self.subtasks = subtasks

        # Apply the custom CSS for scrollable subtasks
        st.markdown("""
            <style>
            .scrollable-panel {
                width: 100%;
                max-height: 300px; /* Set max height */
                padding: 20px;
                border: 2px solid white;
                border-radius: 10px;
                background-color: black;
                color: white;
                box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.5);
                overflow-y: auto;  /* Enable vertical scrolling */
            }

            .scrollable-panel h3, .scrollable-panel h4, .scrollable-panel p {
                color: white;
            }
            </style>
        """, unsafe_allow_html=True)

        # Populate the grid with subtasks
        for subtask in subtasks:
            i = (int(subtask['subtask_id']) - 1)//2  # Determine the row index
            j = (int(subtask['subtask_id']) - 1)%2   # Determine the column index
            
            # Populate the markdown with scrollable sections
            grid[i][j].markdown(
                f'''
                <div class="scrollable-panel">
                    <h3>Group {subtask['group_id']}</h3>
                    <h4>SubTask {subtask['subtask_id']}</h4>
                    <p>{subtask['subtask_description']}</p>
                </div>
                ''', 
                unsafe_allow_html=True
            )

    def update_group_section(self, group_id, group_results):
        for subtask_id, subtask_result in group_results.items():
            i = (int(subtask_id) - 1)//2  # Determine the row index
            j = (int(subtask_id) - 1)%2   # Determine the column index
            
            # Populate the markdown with scrollable content when updating
            self.group_placeholders[i][j].markdown(
                f'''
                <div class="scrollable-panel">
                    <h3>Group {group_id}</h3>
                    <h4>SubTask {subtask_id}</h4>
                    <p>{self.subtasks[int(subtask_id)-1]['subtask_description']}</p>
                    <p>{subtask_result['output']}</p>
                </div>
                ''', 
                unsafe_allow_html=True
            )

    async def run_acp(self, user_query, execution_blueprint):
        # Display the group subtasks
        self.create_group_sections(execution_blueprint)

        # Iterate through the groups asynchronously
        async for group_id, group_results in self.ACP.run(user_query, execution_blueprint):
            self.output[group_id] = group_results
            # Update the group as completed
            self.update_group_section(group_id, group_results)

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