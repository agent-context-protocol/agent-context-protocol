from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.teams.magentic_one import MagenticOne
from autogen_agentchat.ui import Console
import asyncio
import traceback

async def browser_tools_function(dict_body, interpreter_bool = False):
    response_dict = {}

    # Validate input
    if "query" not in dict_body:
        response_dict["status_code"] = 400
        response_dict["text"] = "Missing required parameter 'query'"
        return response_dict



    task = dict_body["query"]
    hil_mode = False
    if interpreter_bool:
        task = f"""{task}\nIf you are unable to solve the question, make a well-informed EDUCATED GUESS based on the information we have provided. 
                    1. **Main Instruction**  
                    You have to only suggest sub-tasks/sub-queries for solving the main query and strictly not provide the solution yourself. For your context, propose the sub-tasks/sub-queries required to address the user’s query thoroughly. Carefully analyze the query and suggest the most logical and appropriate sub-tasks/sub-queries which, if solved, would lead to answering the main query. 

                    2. **Disentangle the Query**  
                    Disentangle the query into different sub-tasks/sub-queries so that each is an independent part of the main query—avoid combining unrelated issues into a single sub-task, as it increases confusion. Also, do not create too many sub-tasks/sub-queries unnecessarily. For example, do not break down a single web-search task into multiple smaller sub-tasks that repeat the same step.  
                    Similarly, when handling files, retrieving and analyzing the file information should be combined into one sub-task or sub-query, without splitting it into separate ones for verification or redundant analysis. All necessary actions for a single file (e.g., reviewing, matching, or referencing) must be contained within that one sub-task/sub-query. There is absolutely no need for verification-based steps, so please do not add them.

                    3. **Avoid Data-Loading Sub-Tasks**  
                    Do not include a separate sub-task just for loading or importing data. Assume that the details for the file paths and attachments are already available wherever needed.

                    4. **Tools Available**  
                    You have two tools at your disposal:
                    - BrowserTools: A web search engine that can retrieve and synthesize information from multiple sources into a concise response. It can also handle image-based question answering, coding assistance, and code execution.  
                    - ReasoningAgent: An agent for deep thinking on problems that can be solved with pure reasoning, without requiring web searches.
                    - CalculatorAgent: Use this function as a calculator agent to get precise answers for the calculation to be performed as described by the user. This agent uses python coding for perfoming the calculations.

                    6. **Tool Selection**  
                    For each sub-task/sub-query, specify which tool (BrowserTools or ReasoningAgent) is best suited. Use ReasoningAgent for purely reasoning-based tasks; if some prior knowledge or outside information is assumed, use BrowserTools instead. And use CalculatorAgent for all important calculations.

                    DO NOT OUTPUT 'I don't know', 'Unable to determine', etc."""

    try:
        # Initialize the ChatCompletionClient
        client = OpenAIChatCompletionClient(model="gpt-4o")

        # Initialize MagenticOne with or without HIL mode
        m1 = MagenticOne(client=client, hil_mode=hil_mode)
        result = await Console(m1.run_stream(task=task))

        # Return the result
        response_dict["status_code"] = 200
        response_dict["text"] = result
        print("API response was:", result)
    except Exception as e:
        error_trace = traceback.format_exc()
        response_dict["status_code"] = 500
        response_dict["text"] = f"An error occurred: {str(e)}"
        print("Error trace:", error_trace)

    return response_dict


MAGENTIC_ONE_API_FUNCTION_DOCS = """Function: magentic_one_api_response

Description:
This function interacts with the MagenticOne multi-agent system to autonomously execute a user-specified task. The system utilizes various agents, including FileSurfer, WebSurfer, Coder, and Executor, to solve open-ended tasks. 

Use Case:
Use this function to automate tasks that require coordination between multiple agents, such as writing code, fetching web data, or processing files. It provides a unified interface to interact with the MagenticOne system and obtain results for complex tasks.

Parameters:
- **query** (string, required): The specific task to be executed by MagenticOne (e.g., "Write a Python script to fetch data from an API").
Expected Output:
- **text** (string): The result of the task execution or an error message if the function fails.

Example Usage:
```python
response = magentic_one_api_response("What are the latest advancements in AI?")
"""

