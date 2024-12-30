from available_apis.browser_tools.main import reasoning_agent_function #, browser_tools_function
from available_apis.browser_tools_hf.GAIA.main import browser_tools_function

# BROWSER_TOOLS_FUNCTION_DOCS = """Function: browser_tools_function

# Description:
# This function interacts with the BrowserTools API to generate a concise answer to a user's query by searching the web and synthesizing information from multiple sources. It can be used for accesing attachments via downloading as well.

# Use Case:
# Use this function as a web search engine to retrieve and compile information into a single, coherent response for queries that require up-to-date or broad information from the internet. 
# For best results do not ask too much information in one search, rather break down the query and do multiple searches.
# It can be used for accesing attachments via downloading as well.

# Parameters:
# - **query** (string, required): The user's question or search term that needs to be answered using web data.

# Expected Output:
# - **response_content** (string): A compiled answer based on web search results provided by the API.

# Example Usage:
# 1. response = browser_tools_function("What is the capital of India?")
# 2. When we need to use this function for downloading files then please structure the queries like below strictly:
# response = browser_tools_function("Download and return the raw contents of: file:///Users/aarjun1/Documents/Arjun/Princeton_Work/newCode/interpreter-translator-rapid_apis_GAIA_Simple/GAIA/2023/validation/32102e3e-d12a-4209-9163-7b3a104efe5d.xlsx")
# """

BROWSER_TOOLS_FUNCTION_DOCS = """Function: browser_tools_function

Description:
This function interacts with the BrowserTools API to generate a concise answer to a user's query by searching the web and synthesizing information from multiple sources. It can also function as a reasoning agent and assist in writing and executing code (coding agent).

Use Case:
Use this function as a web search engine to retrieve and compile information into a single, coherent response for queries that require up-to-date or broad information from the internet. It can also be utilized for reasoning tasks and coding assistance, including code writing and execution. For best results, do not ask for too much information in one search; rather, break down the query and perform multiple searches. Please provide the full context in the query itself and avoid vaguely mentioning things about which there is no context. For image analysisi please always provide the image filepath else there is not point.

Parameters:
- **query** (string, required): The user's question or search term that needs to be answered using web data.

Expected Output:
- **response_content** (string): A compiled answer based on web search results provided by the API, or the result of code execution if used as a coding agent.

Example Usage:
1. response = browser_tools_function("What is the capital of India?")
2. response = browser_tools_function("Write a Python function that calculates the factorial of a number.")
"""

REASONING_AGENT_FUNCTION_DOCS = """Function: reasoning_agent_function

Description:
This function acts as reasoming agent and tries to generate a concise answer to a user's query by by reasoning over the information provided.

Use Case:
Use this function as a reasoming agent to deeply think about a reasoning problem which does not require web search and rather can be solved through pure reasoning.

Parameters:
- **query** (string, required): The user's question that needs to be answered via reasoning.

Expected Output:
- **response_content** (string): A compiled answer.

Example Usage:
1. response = reasoning_agent_function("There are 12 identical balls, one of which is slightly heavier than the others. You have a balance scale and need to find the heavier ball in just 3 weighings. How can you do it?")
2. response = reasoning_agent_function("Consider a game where you can make moves either adding 1 or multiplying by 2 starting from 1, and you must reach exactly 100. What is the minimum number of moves needed, and what sequence of moves achieves this?")
3. response = reasoning_agent_function("If a train travels at a speed of 60 km/h and covers a distance of 180 km, how long does the journey take?")
"""

BROWSER_FUNCTION_DOCUMENTATION_DICT = {
    "BrowserTools": BROWSER_TOOLS_FUNCTION_DOCS,
    "ReasoningAgent": REASONING_AGENT_FUNCTION_DOCS,
    }
BROSWER_FUNCTION_DICT = {
    "BrowserTools": browser_tools_function,
    "ReasoningAgent": reasoning_agent_function,
    }

BROSWER_FUNCTION_REQD_PARAMS_DICT = {
    "BrowserTools": {"query": {"type": "string"}},
    "ReasoningAgent": {"query": {"type": "string"}},
}

BROSWER_FUNCTION_PARAMS_DICT = {
    "BrowserTools": {"query": {"type": "string"}},
    "ReasoningAgent": {"query": {"type": "string"}},
}