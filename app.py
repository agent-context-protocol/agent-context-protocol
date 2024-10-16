import streamlit as st
import asyncio
from orchestrator import MainOrchestrator

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

        /* Panel max height with scrollable content */
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


class StreamlitOrchestrator:
    def __init__(self):
        self.orchestrator = MainOrchestrator()
        self.output = {}
        self.group_placeholders = {}
        self.panels = []

    def create_group_sections(self, workflow):
        panels = []

        for group_id in workflow.keys():
            for translator_id in workflow[group_id].keys():
                panels.append({
                    'group_id' : group_id,
                    'panel_id' : translator_id,
                    'panel_description' : workflow[group_id][translator_id]['panel_description']}
                )

        grid = []
        for i in range(len(panels)//2 + 1):
            cols = st.columns(2)  # Fixed 2 columns per row
            grid_row = []
            
            for j in range(2):
                container = cols[j].empty()  # Create an empty container for each column
                grid_row.append(container)
            grid.append(grid_row)

        self.group_placeholders = grid
        self.panels = panels

        # Apply the custom CSS for scrollable panels
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

        # Populate the grid with panels
        for panel in panels:
            i = (int(panel['panel_id']) - 1)//2  # Determine the row index
            j = (int(panel['panel_id']) - 1)%2   # Determine the column index
            
            # Populate the markdown with scrollable sections
            grid[i][j].markdown(
                f'''
                <div class="scrollable-panel">
                    <h3>Group {panel['group_id']}</h3>
                    <h4>Panel {panel['panel_id']}</h4>
                    <p>{panel['panel_description']}</p>
                </div>
                ''', 
                unsafe_allow_html=True
            )

    def update_group_section(self, group_id, group_results):
        for panel_id, panel_result in group_results.items():
            i = (int(panel_id) - 1)//2  # Determine the row index
            j = (int(panel_id) - 1)%2   # Determine the column index
            
            # Populate the markdown with scrollable content when updating
            self.group_placeholders[i][j].markdown(
                f'''
                <div class="scrollable-panel">
                    <h3>Group {group_id}</h3>
                    <h4>Panel {panel_id}</h4>
                    <p>{self.panels[int(panel_id)-1]['panel_description']}</p>
                    <p>{panel_result['output']}</p>
                </div>
                ''', 
                unsafe_allow_html=True
            )

    async def run_orchestrator(self, user_query, workflow):
        # Display the group panels
        self.create_group_sections(workflow)

        # Iterate through the groups asynchronously
        async for group_id, group_results in self.orchestrator.run(user_query, workflow):
            self.output[group_id] = group_results
            # Update the group as completed
            self.update_group_section(group_id, group_results)

async def main():
    # Load custom CSS
    load_css()

    st.title("Workflow Orchestrator")
    orchestrator = StreamlitOrchestrator()

    # Sidebar for user input
    with st.sidebar:
        st.header("User Input")
        user_query = st.text_area("Enter your query:")
        if st.button("Example Query"):
            user_query = "Example query"

    if st.button("Run Workflow"):
        with st.spinner("Running workflow... please wait"):
            st.write("Running workflow...")
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Initialize the workflow
            workflow = await orchestrator.orchestrator.initialise(user_query)

            async def update_progress():
                total_groups = len(orchestrator.orchestrator.main_translator.workflow)
                while True:
                    completed_groups = len(orchestrator.output)
                    progress = completed_groups / total_groups
                    progress_bar.progress(progress)
                    status_text.text(f"Completed {completed_groups} out of {total_groups} groups")
                    if progress >= 1.0:
                        break
                    await asyncio.sleep(0.1)

            # Run the orchestrator and update progress simultaneously
            await asyncio.gather(
                orchestrator.run_orchestrator(user_query, workflow),
                update_progress()
            )

            st.success("Workflow completed!")

if __name__ == "__main__":
    asyncio.run(main())