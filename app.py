import streamlit as st
import asyncio
from orchestrator import MainOrchestrator
import math

class StreamlitOrchestrator:
    def __init__(self):
        self.orchestrator = MainOrchestrator()
        self.output = {}
        self.group_placeholders = {}

    def create_group_sections(self):
        workflow = self.orchestrator.main_translator.workflow
        num_groups = len(workflow)
        num_cols = 3  # You can adjust this number to change the number of columns
        num_rows = math.ceil(num_groups / num_cols)
        
        # Create a grid of columns
        cols = st.columns(num_cols)
        
        # Populate the grid with placeholders
        for i, group_id in enumerate(workflow.keys()):
            with cols[i % num_cols]:
                self.group_placeholders[str(group_id)] = st.empty()

    async def run_orchestrator(self, user_query):
        workflow = await self.orchestrator.initialise(user_query)
        self.create_group_sections()
        async for group_id, group_results in self.orchestrator.run(user_query):
            self.output[group_id] = group_results
            self.update_group_section(group_id, group_results)

    def update_group_section(self, group_id, group_results):
        print(self.group_placeholders.keys())
        print(group_id)
        with self.group_placeholders[group_id].container():
            st.subheader(f"Group {group_id}")
            for panel_id, panel_result in group_results.items():
                st.write(f"Panel {panel_id}:")
                st.write(f"Description: {panel_result['panel_description']}")
                st.write(f"Output:")
                st.write(panel_result['output'])
                st.write("---")

async def main():
    st.title("Workflow Orchestrator")

    orchestrator = StreamlitOrchestrator()

    user_query = st.text_input("Enter your query:")

    if st.button("Run Workflow"):
        st.write("Running workflow...")
        progress_bar = st.progress(0)
        status_text = st.empty()

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
            orchestrator.run_orchestrator(user_query),
            update_progress()
        )

        st.success("Workflow completed!")

if __name__ == "__main__":
    asyncio.run(main())