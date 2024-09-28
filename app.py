import streamlit as st
import asyncio
from orchestrator import MainOrchestrator

class StreamlitOrchestrator:
    def __init__(self):
        self.orchestrator = MainOrchestrator()
        self.output = {}

    async def run_orchestrator(self, user_query):
        async for group_id, group_results in self.orchestrator.run(user_query):
            self.output[group_id] = group_results

    def display_results(self):
        for group_id, group_results in self.output.items():
            st.subheader(f"Group {group_id}")
            for panel_id, panel_result in group_results.items():
                st.write(f"Panel {panel_id}:")
                st.write(f"Description: {panel_result['panel_description']}")
                st.write(f"Output:")
                st.write(panel_result['output'])  # Display the text returned by build_verify()
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
            total_panels = sum(len(group) for group in orchestrator.orchestrator.main_translator.workflow.values())
            while True:
                completed_panels = sum(len(group_results) for group_results in orchestrator.output.values())
                progress = completed_panels / total_panels
                progress_bar.progress(progress)
                status_text.text(f"Completed {completed_panels} out of {total_panels} panels")
                if progress >= 1.0:
                    break
                await asyncio.sleep(0.1)

        # Run the orchestrator and update progress simultaneously
        await asyncio.gather(
            orchestrator.run_orchestrator(user_query),
            update_progress()
        )

        st.success("Workflow completed!")

    orchestrator.display_results()

if __name__ == "__main__":
    asyncio.run(main())