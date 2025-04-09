import streamlit as st
import asyncio
from acp_manager import ACP
from available_tools.browser_tools.mdconvert import MarkdownConverter, UnsupportedFormatException, FileConversionException
import re

st.set_page_config(layout = "wide") 


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
        self.orchestrator = ACP()
        self.output = {}
        self.group_placeholders = {}
        self.panels = []

    # Function to create group sections with minimal panel layout
    def create_group_sections(self, workflow):
        # Panels will hold information about each group and its translators
        panels = []

        # Iterate through the workflow dictionary and collect panel information
        for group_id in workflow.keys():
            if group_id == "user_query":
                continue
            for translator_id in workflow[group_id].keys():
                panels.append({
                    'group_id' : group_id,
                    'panel_id' : translator_id,
                    'subtask_description' : workflow[group_id][translator_id]['subtask_description']}
                )

        # Create a grid layout to hold the panels
        grid = []
        for i in range(len(panels)//2 + 1):
            cols = st.columns(2)  # Create two columns per row
            grid_row = []
            
            for j in range(2):
                container = cols[j].empty()  # Create an empty container for each column
                grid_row.append(container)
            grid.append(grid_row)

        self.group_placeholders = grid

        self.panels = panels

        # Apply the custom CSS class to style the panels with black background and white text
        st.markdown("""
            <style>
            .fixed-panel {
                width: 100%;  /* Take up 100% of the column width (i.e., half the page) */
                height: 500px; /* Allow height to adjust dynamically based on content */
                padding: 20px;
                border: 2px solid white;  /* White boundary */
                border-radius: 10px;  /* Rounded corners */
                background-color: black; /* Black background */
                color: white; /* White text */
                box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.5);  /* Optional shadow */
            }

            /* Ensure headings and paragraphs are white */
            .fixed-panel h3, .fixed-panel h4, .fixed-panel p {
                color: white; /* White text for headings and paragraph */
            }
            </style>
        """, unsafe_allow_html=True)

        # Populate the grid with panels
        for panel in panels:
            i = (int(panel['panel_id']) - 1)//2  # Determine the row index
            j = (int(panel['panel_id']) - 1)%2   # Determine the column index
            
            # Populate the markdown with fixed-size sections, black background, and white text
            grid[i][j].markdown(
                f'''
                <div class="fixed-panel">
                    <h3>Group {panel['group_id']}</h3>
                    <h4>Panel {panel['panel_id']}</h4>
                    <p>{panel['subtask_description']}</p>
                </div>
                ''', 
                unsafe_allow_html=True
            )

        # st.markdown('<div class="grid-container">', unsafe_allow_html=True)
        # for group_id, group in workflow.items():
        #     group_description = f"Group {group_id}"  # Group number

        #     # Create a panel for each group with no extra box styling
        #     with st.container():
        #         st.write(f"### {group_description}")  # Display the group number
                
        #         # Iterate through each panel within the group and display the descriptions
        #         for panel_id, panel_info in group.items():
        #             subtask_description = panel_info["subtask_description"]
        #             st.write(f"**Panel {panel_id}**: {subtask_description}")
                    
        #             # Store placeholders for each panel to update later
        #             self.group_placeholders[str(group_id)] = st.empty()
                    
        # st.markdown('</div>', unsafe_allow_html=True)

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
        st.markdown("""
            <style>
            .completed-panel {
                width: 100%;  /* Take up 100% of the column width (i.e., half the page) */
                height: 500px; /* Fixed height to allow scrolling */
                padding: 20px;
                border: 2px solid white;  /* White boundary */
                border-radius: 10px;  /* Rounded corners */
                background-color: black; /* Black background */
                color: white; /* White text */
                box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.5);  /* Optional shadow */
                overflow-y: auto; /* Enable vertical scrolling */
            }

            /* Ensure headings and paragraphs are white */
            .completed-panel h3, .completed-panel h4, .completed-panel p {
                color: white; /* White text for headings and paragraph */
            }
            
            /* Optional: Customize the scrollbar */
            .completed-panel::-webkit-scrollbar {
                width: 8px;
            }

            .completed-panel::-webkit-scrollbar-thumb {
                background-color: #888; 
                border-radius: 10px;
            }

            .completed-panel::-webkit-scrollbar-thumb:hover {
                background-color: #555; 
            }

            </style>
        """, unsafe_allow_html=True)
        
        for panel_id, panel_result in group_results.items():
            i = (int(panel_id) - 1)//2  # Determine the row index
            j = (int(panel_id) - 1)%2   # Determine the column index
            
            # Populate the markdown with fixed-size sections, black background, and white text
            self.group_placeholders[i][j].markdown(
                f'''
                <div class="completed-panel">
                    <h3>Group {group_id}</h3>
                    <h4>Panel {panel_id}</h4>
                    <p>{self.panels[int(panel_id)-1]['subtask_description']}</p>
                    <p>{panel_result['output']}</p>
                </div>
                ''', 
                unsafe_allow_html=True
            )


        # with self.group_placeholders[group_id].container():
        #     # st.write(f"#### Group {group_id} (Completed)")
        #     # Create an expander for showing the outputs
        #     with st.expander(f"View Results for Group {group_id}"):
        #         for panel_id, panel_result in group_results.items():
        #             st.markdown(f"**Panel {panel_id}**: {panel_result['subtask_description']}")
        #             # st.write("**Output:**")
        #             st.write(panel_result['output'])
        #             st.write("---")

def extract_file_path(query):
    match = re.search(r'Attachment: file://(\S+)', query)
    if match:
        return match.group(1)
    else:
        return None
    
def reformat_query_with_attachment_content(user_query):

    mdconvert_obj = MarkdownConverter()

    # Check if there's an attachment and extract the file path
    file_path = extract_file_path(user_query)
    
    # Convert the file content
    res = mdconvert_obj.convert_local(file_path)
    
    # Reformat the query with the question and attachment content
    reformatted_query = f"question: {user_query.split('Attachment: file://')[0].strip()}\n"
    reformatted_query += f"Attachment File Content:\n{res.text_content}"
    
    # # Display extracted details for confirmation
    # print("Result title:", res.title)
    # print("Result text content:", res.text_content)
    
    return reformatted_query

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

    # if user query has a file attachement
    if "Attachment: file://" in user_query:
        user_query = reformat_query_with_attachment_content(user_query)
        print("user_query : ",user_query)
        # print(cause_Error)
        

    if st.button("Run Workflow"):
        with st.spinner("Running workflow... please wait"):
            st.write("Running workflow...")
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Initialize the workflow
            workflow = await orchestrator.orchestrator.initialise(user_query)

            async def update_progress():
                total_groups = len(orchestrator.orchestrator.dag_compiler.execution_blueprint)
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