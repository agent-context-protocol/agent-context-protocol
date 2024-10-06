import streamlit as st
import asyncio
from orchestrator import MainOrchestrator

# Load custom CSS for minimal styling (removing extra background colors and padding)
def load_css():
    st.markdown("""
        <style>
        /* Grid styling */
        .grid-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr); /* Create three equal columns */
            gap: 20px;
            padding: 10px;
        }

        .grid-item {
            padding: 15px;
            background-color: #f1f1f1;
            border-radius: 8px;
            text-align: left;
            box-shadow: none;
            height: auto;
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

        </style>
    """, unsafe_allow_html=True)

class StreamlitOrchestrator:
    def __init__(self):
        self.orchestrator = MainOrchestrator()
        self.output = {}
        self.group_placeholders = {}

    # Function to create group sections with minimal panel layout
    def create_group_sections(self, workflow):
        st.markdown('<div class="grid-container">', unsafe_allow_html=True)
        for group_id, group in workflow.items():
            group_description = f"Group {group_id}"  # Group number

            # Create a panel for each group with no extra box styling
            with st.container():
                st.write(f"### {group_description}")  # Display the group number
                
                # Iterate through each panel within the group and display the descriptions
                for panel_id, panel_info in group.items():
                    panel_description = panel_info["panel_description"]
                    st.write(f"**Panel {panel_id}**: {panel_description}")
                    
                    # Store placeholders for each panel to update later
                    self.group_placeholders[str(group_id)] = st.empty()
                    
        st.markdown('</div>', unsafe_allow_html=True)

    async def run_orchestrator(self, user_query, workflow):
        # Display the group panels
        self.create_group_sections(workflow)

        # Iterate through the groups asynchronously
        async for group_id, group_results in self.orchestrator.run(user_query, workflow):
            self.output[group_id] = group_results
            # Update the group as completed
            self.update_group_section(group_id, group_results)

    # Function to update the group panel and display results
    def update_group_section(self, group_id, group_results):
        with self.group_placeholders[group_id].container():
            # st.write(f"#### Group {group_id} (Completed)")
            # Create an expander for showing the outputs
            with st.expander(f"View Results for Group {group_id}"):
                for panel_id, panel_result in group_results.items():
                    st.markdown(f"**Panel {panel_id}**: {panel_result['panel_description']}")
                    # st.write("**Output:**")
                    st.write(panel_result['output'])
                    st.write("---")

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
