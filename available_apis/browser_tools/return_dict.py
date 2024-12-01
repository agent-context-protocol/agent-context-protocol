from available_apis.browser_tools.main import browser_tools_function

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
Use this function as a web search engine to retrieve and compile information into a single, coherent response for queries that require up-to-date or broad information from the internet. It can also be utilized for reasoning tasks and coding assistance, including code writing and execution. For best results, do not ask for too much information in one search; rather, break down the query and perform multiple searches. Please provide the full context in the query itself and avoid vaguely mentioning things about which there is no context.

Parameters:
- **query** (string, required): The user's question or search term that needs to be answered using web data.

Expected Output:
- **response_content** (string): A compiled answer based on web search results provided by the API, or the result of code execution if used as a coding agent.

Example Usage:
1. response = browser_tools_function("What is the capital of India?")
2. response = browser_tools_function("Write a Python function that calculates the factorial of a number.")
"""


BROWSER_FUNCTION_DOCUMENTATION_DICT = {
    "BrowserTools": BROWSER_TOOLS_FUNCTION_DOCS
    }
BROSWER_FUNCTION_DICT = {
    "BrowserTools": browser_tools_function
    }

BROSWER_FUNCTION_REQD_PARAMS_DICT = {
    "BrowserTools": {"query": {"type": "string"}},
}

BROSWER_FUNCTION_PARAMS_DICT = {
    "BrowserTools": {"query": {"type": "string"}},
}