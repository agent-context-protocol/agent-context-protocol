# THIS IS EXPERIMENTAL! IT RELIES ON A NON-YET-MERGED BRANCH OF TRANFORMERS? IT WONT WORK OUT OF THE BOX.


import asyncio
import os
from typing import Optional
import pandas as pd
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import datasets
from huggingface_hub import login
from transformers.agents import ReactCodeAgent, ReactJsonAgent
from transformers.agents.agents import DEFAULT_REACT_JSON_SYSTEM_PROMPT
from transformers.agents.default_tools import Tool, PythonInterpreterTool
from transformers.agents.llm_engine import MessageRole
from langchain_openai import ChatOpenAI
from langchain_openai import AzureChatOpenAI
from langchain_community.cache import SQLiteCache
from available_apis.browser_tools_hf.GAIA.scripts.tools.web_surfer import (
    SearchInformationTool,
    NavigationalSearchTool,
    VisitTool,
    PageUpTool,
    PageDownTool,
    FinderTool,
    FindNextTool,
    ArchiveSearchTool,
)
from available_apis.browser_tools_hf.GAIA.scripts.tools.mdconvert import MarkdownConverter
from available_apis.browser_tools_hf.GAIA.scripts.reformulator import prepare_response
from available_apis.browser_tools_hf.GAIA.scripts.run_agents import answer_questions
from available_apis.browser_tools_hf.GAIA.scripts.tools.visual_qa import VisualQATool, VisualQAGPT4Tool, visualizer
from available_apis.browser_tools_hf.GAIA.scripts.llm_engines import OpenAIEngine, AnthropicEngine, NIMEngine
import os
from typing import Tuple, Any, List
import re
import sqlite3
from transformers.agents.agents import ManagedAgent
from langchain_core.outputs import LLMResult
# import ray
# ray.init()

from datasets import load_dataset

from rich import print as pp
from rich.console import Console
from rich.table import Table
from rich import box
import base64

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_openai import AzureChatOpenAI
from langchain_community.cache import SQLiteCache
from langchain_core.callbacks import BaseCallbackHandler
import requests
from openai import OpenAI

from autogen.code_utils import execute_code
import autogen
from autogen.agentchat.contrib.society_of_mind_agent import SocietyOfMindAgent

from available_apis.browser_tools.browser_utils import SimpleTextBrowser

MODEL='gpt-4o-2024-08-06'
DATA_NAME = '2023_level1'
SPLIT = 'validation'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_BASE = os.getenv('OPENAI_API_BASE')
BING_API_KEY = os.getenv('BING_API_KEY')
SERPAPI_KEY = os.environ["SERPAPI_API_KEY"]

class TextInspectorTool(Tool):
    text_limit = 70000
    websurfer_llm_engine = OpenAIEngine()


    name = "inspect_file_as_text"
    description = """
You cannot load files yourself: instead call this tool to read a file as markdown text and ask questions about it.
This tool handles the following file extensions: [".html", ".htm", ".xlsx", ".pptx", ".wav", ".mp3", ".flac", ".pdf", ".docx"], and all other types of text files. IT DOES NOT HANDLE IMAGES."""

    inputs = {
        "question": {
            "description": "[Optional]: Your question, as a natural language sentence. Provide as much context as possible. Do not pass this parameter if you just want to directly return the content of the file.",
            "type": "string",
        },
        "file_path": {
            "description": "The path to the file you want to read as text. Must be a '.something' file, like '.pdf'. If it is an image, use the visualizer tool instead! DO NOT USE THIS TOOL FOR A WEBPAGE: use the search tool instead!",
            "type": "string",
        },
    }
    output_type = "string"
    md_converter = MarkdownConverter()

    def forward_initial_exam_mode(self, file_path, question):
        result = self.md_converter.convert(file_path)

        if file_path[-4:] in ['.png', '.jpg']:
            raise Exception("Cannot use inspect_file_as_text tool with images: use visualizer instead!")

        if ".zip" in file_path:
            return result.text_content
        
        if not question:
            return result.text_content
        
        messages = [
            {
                "role": MessageRole.SYSTEM,
                "content": "Here is a file:\n### "
                + str(result.title)
                + "\n\n"
                + result.text_content[:self.text_limit],
            },
            {
                "role": MessageRole.USER,
                "content": question,
            },
        ]
        return self.websurfer_llm_engine(messages)

    def forward(self, file_path, question: Optional[str] = None) -> str:

        result = self.md_converter.convert(file_path)

        if file_path[-4:] in ['.png', '.jpg']:
            raise Exception("Cannot use inspect_file_as_text tool with images: use visualizer instead!")

        if ".zip" in file_path:
            return result.text_content
        
        if not question:
            return result.text_content
        
        messages = [
            {
                "role": MessageRole.SYSTEM,
                "content": "You will have to write a short caption for this file, then answer this question:"
                + question,
            },
            {
                "role": MessageRole.USER,
                "content": "Here is the complete file:\n### "
                + str(result.title)
                + "\n\n"
                + result.text_content[:self.text_limit],
            },
            {
                "role": MessageRole.USER,
                "content": "Now answer the question below. Use these three headings: '1. Short answer', '2. Extremely detailed answer', '3. Additional Context on the document and question asked'."
                + question,
            },
        ]
        return self.websurfer_llm_engine(messages)
    
# @ray.remote
class GAIA_Agent:
    def __init__(self, interpreter_bool=False):
        proprietary_llm_engine = OpenAIEngine()
        # Replace with OAI if needed
        websurfer_llm_engine = proprietary_llm_engine

        WEB_TOOLS = [
            SearchInformationTool(),
            NavigationalSearchTool(),
            VisitTool(),
            PageUpTool(),
            PageDownTool(),
            FinderTool(),
            FindNextTool(),
            ArchiveSearchTool(),
        ]

        text_limit = 70000

        surfer_agent = ReactJsonAgent(
            llm_engine=websurfer_llm_engine,
            tools=WEB_TOOLS,
            max_iterations=10,
            verbose=2,
            # grammar = DEFAULT_JSONAGENT_REGEX_GRAMMAR,
            system_prompt=DEFAULT_REACT_JSON_SYSTEM_PROMPT,
            planning_interval=4,
            plan_type="default",
        )

        search_agent = ManagedAgent(
            surfer_agent,
            "web_search",
            description="""A team member that will browse the internet to answer your question.
        Ask him for all your web-search related questions, but he's unable to do problem-solving.
        Provide him as much context as possible, in particular if you need to search on a specific timeframe!
        And don't hesitate to provide him with a complex search task, like finding a difference between two webpages.""",
            additional_prompting="""You can navigate to .txt or .pdf online files using your 'visit_page' tool.
        If it's another format, you can return the url of the file, and your manager will handle the download and inspection from there.
        Additionally, if after some searching you find out that you need more information to answer the question, you can use `final_answer` with your request for clarification as argument to request for more information.""",
            provide_run_summary=True
        )

        ti_tool = TextInspectorTool()

        TASK_SOLVING_TOOLBOX = [
            visualizer,  # VisualQATool(),
            ti_tool,
        ]


        self.llm_engine = proprietary_llm_engine

        self.react_agent = ReactCodeAgent(
            llm_engine=self.llm_engine,
            tools=TASK_SOLVING_TOOLBOX,
            max_iterations=12,
            verbose=0,
            # grammar=DEFAULT_CODEAGENT_REGEX_GRAMMAR,
            additional_authorized_imports=[
                "requests",
                "zipfile",
                "os",
                "pandas",
                "numpy",
                "sympy",
                "json",
                "bs4",
                "pubchempy",
                "xml",
                "yahoo_finance",
                "Bio",
                "sklearn",
                "scipy",
                "pydub",
                "io",
                "PIL",
                "chess",
                "PyPDF2",
                "pptx",
                "torch",
                "datetime",
                "csv",
                "fractions",
            ],
            planning_interval=4,
            managed_agents=[search_agent]
        )

        self.interpreter_bool = interpreter_bool

        agent1 = autogen.ConversableAgent(
            name="Actor",
            system_message='''You are a helpful assistant.  When answering a question, you must explain your thought process step by step before answering the question. When others make suggestions about your answers, think carefully about whether or not to adopt the opinions of others.
If you are unable to solve the question, make a well-informed EDUCATED GUESS based on the information we have provided.  DO NOT OUTPUT 'I don't know', 'Unable to determine', etc.''',
            # llm_config={"config_list": [{"model": MODEL, "api_type": "azure", "api_version": "2024-04-01-preview", "temperature": 0.1, "api_key": AZURE_OPENAI_API_KEY, "base_url": AZURE_OPENAI_ENDPOINT}]},
            llm_config={"config_list": [{"model": MODEL, "temperature": 0.1, "api_key": OPENAI_API_KEY, "base_url": OPENAI_API_BASE}]},
            is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
        )

        agent2 = autogen.ConversableAgent(
            name="Critic",
            system_message='''You are a helpful assistant.You want to help others spot logical or intellectual errors. When and only when you can't find a logical flaw in the other person's reasoning, you should say "TERMINATE" to end the conversation.''',
            # llm_config={"config_list": [{"model": MODEL, "api_type": "azure", "api_version": "2024-04-01-preview", "temperature": 0, "api_key": AZURE_OPENAI_API_KEY, "base_url": AZURE_OPENAI_ENDPOINT}]},
            llm_config={"config_list": [{"model": MODEL, "temperature": 0, "api_key": OPENAI_API_KEY, "base_url": OPENAI_API_BASE}]},
        )

        groupchat = autogen.GroupChat(
            agents=[agent1, agent2],
            messages=[],
            speaker_selection_method="round_robin",
            allow_repeat_speaker=False,
            max_round=8,
        )

        manager = autogen.GroupChatManager(
            groupchat=groupchat,
            is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
            # llm_config={"config_list": [{"model": MODEL, "api_type": "azure", "api_version": "2024-04-01-preview", "temperature": 0.0, "api_key": AZURE_OPENAI_API_KEY, "base_url": AZURE_OPENAI_ENDPOINT}]},
            llm_config={"config_list": [{"model": MODEL, "temperature": 0.0, "api_key": OPENAI_API_KEY, "base_url": OPENAI_API_BASE}]},
        )

        self.society_of_mind_agent = SocietyOfMindAgent(
            "society_of_mind",
            chat_manager=manager,
            # llm_config={"config_list": [{"model": MODEL, "api_type": "azure", "api_version": "2024-04-01-preview", "temperature": 0.0, "api_key": AZURE_OPENAI_API_KEY, "base_url": AZURE_OPENAI_ENDPOINT}]}
            llm_config={"timeout": 350, "config_list": [{"model": MODEL, "temperature": 0.0, "api_key": OPENAI_API_KEY, "base_url": OPENAI_API_BASE}]}
        )

        self.user_proxy = autogen.UserProxyAgent(
            "user_proxy",
            human_input_mode="NEVER",
            code_execution_config=False,
            default_auto_reply="",
            is_termination_msg=lambda x: True,
        )

    def call_transformers(self, agent, question: str, **kwargs) -> str:
        result = agent.run(question, **kwargs)
        agent_memory = agent.write_inner_memory_from_logs(summary_mode=True)
        intermediate_steps =  [f"{key}: {value}" for log in agent.logs for key, value in log.items() if key != "agent_memory"]
        return intermediate_steps

    def ask(self, raw_question: str, attachment_name: str = None) -> str:
        
        steps = []

        if attachment_name is not None and attachment_name.strip() != "":
            question = f"{raw_question}\nAttachment: file:///Users/long/workspace/GAIA/2023/{SPLIT}/{attachment_name}"
        else:
            question = raw_question
        pp(f"Question: {question}")

        response = self.call_transformers(self.react_agent, question)


        # if len(steps) == 0:
        if False:
            if self.interpreter_bool:
                answer = self.user_proxy.initiate_chat(
                    self.society_of_mind_agent, 
                    message=f"""{question}\nIf you are unable to solve the question, make a well-informed EDUCATED GUESS based on the information we have provided. 
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

                    5. **Tool Selection**  
                    For each sub-task/sub-query, specify which tool (BrowserTools or ReasoningAgent) is best suited. Use ReasoningAgent for purely reasoning-based tasks; if some prior knowledge or outside information is assumed, use BrowserTools instead.
                    DO NOT OUTPUT 'I don't know', 'Unable to determine', etc.""").summary
            else:
                answer = self.user_proxy.initiate_chat(
                    self.society_of_mind_agent, 
                    message=f"""{question}\nIf you are unable to solve the question, make a well-informed EDUCATED GUESS based on the information we have provided.
                    DO NOT OUTPUT 'I don't know', 'Unable to determine', etc.""").summary
        else:
            if self.interpreter_bool:
                steps_prompt = '\n'.join(response)
                answer = self.user_proxy.initiate_chat(
                    self.society_of_mind_agent, 
                    message=f"""{question}\nTo answer the above question, I did the following:
                    {steps_prompt}

                    Referring to the information I have obtained (which may not be accurate), what do you think is the answer to the question?
                    1. **Main Instruction**  
                    You have to only suggest sub-tasks/sub-queries for solving the main query and strictly not provide the solution yourself. For your context, propose the sub-tasks/sub-queries required to address the user’s query thoroughly. Carefully analyze the query and suggest the most logical and appropriate sub-tasks/sub-queries which, if solved, would lead to answering the main query. Based on your initial web searches, you can recommend well-informed sub-tasks/sub-queries that make the solution path more focused rather than vague, utilizing insights into which searches met expectations and which did not, while providing workarounds where needed.
                    
                    2. **Web-Search Refinements**  
                    If any web search path does not yield relevant information, adapt and find alternative approaches or approximations. Do not be overly strict about a particular path. The ultimate goal is to reach a valid answer, so be flexible with sub-queries as needed.

                    3. **Disentangle the Query**  
                    Disentangle the query into different sub-tasks/sub-queries so that each is an independent part of the main query—avoid combining unrelated issues into a single sub-task, as it increases confusion. Also, do not create too many sub-tasks/sub-queries unnecessarily. For example, do not break down a single web-search task into multiple smaller sub-tasks that repeat the same step.  
                    Similarly, when handling files, retrieving and analyzing the file information should be combined into one sub-task or sub-query, without splitting it into separate ones for verification or redundant analysis. All necessary actions for a single file (e.g., reviewing, matching, or referencing) must be contained within that one sub-task/sub-query. There is absolutely no need for verification-based steps, so please do not add them.

                    4. **Avoid Data-Loading Sub-Tasks**  
                    Do not include a separate sub-task just for loading or importing data. Assume that the details for the file paths and attachments are already available wherever needed.

                    5. **Tools Available**  
                    You have two tools at your disposal:
                    - BrowserTools: A web search engine that can retrieve and synthesize information from multiple sources into a concise response. It can also handle image-based question answering, coding assistance, and code execution.  
                    - ReasoningAgent: An agent for deep thinking on problems that can be solved with pure reasoning, without requiring web searches.

                    6. **Tool Selection**  
                    For each sub-task/sub-query, specify which tool (BrowserTools or ReasoningAgent) is best suited. Use ReasoningAgent for purely reasoning-based tasks; if some prior knowledge or outside information is assumed, use BrowserTools instead.

                    If you are unable to solve the question, make a well-informed EDUCATED GUESS based on the information we have provided.
                    DO NOT OUTPUT 'I don't know', 'Unable to determine', etc.""").summary
            else:
                # steps_prompt = f"{response}"
                steps_prompt = '\n'.join(response)
                answer = self.user_proxy.initiate_chat(
                    self.society_of_mind_agent, 
                    message=f"""{question}\nTo answer the above question, I did the following:
                    {steps_prompt}

                    Referring to the information I have obtained (which may not be accurate), what do you think is the answer to the question?
                    It is ok to be not sure about the answer and provide a partial answer through a vague educated guess based on the information provided, but remember that providing some answer is much better than saying that no answer exists.
                    DO NOT OUTPUT 'I don't know', 'Unable to determine', etc.""").summary
        # formatted_answer = self.format_answer_chain.invoke({'question': question, 'answer': answer})#.answer

        return answer
    

def browser_tools_function(dict_body, interpreter_bool = False):
    response_dict = {}

    if "query" not in dict_body:
        response_dict["status_code"] = 400
        response_dict["text"] = "Missing required parameters query"
        return response_dict
    
    query = dict_body["query"]
    
    gaia_obj = GAIA_Agent(interpreter_bool = interpreter_bool)

    answer = gaia_obj.ask(query)

    response_dict["status_code"] = 200
    response_dict["text"] = answer

    # print("original sybil answerrrr: ",answer)

    return response_dict

# # report check
# # dict_body = {"query": "What is there in the background and forwground of this image in the url: https://images.pexels.com/photos/346885/pexels-photo-346885.jpeg?cs=srgb&dl=pexels-nurseryart-346885.jpg&fm=jpg"}
# dict_body = {"query": "Who won the 2024 us elections and against whom?"}
# res_dict = browser_tools_function(dict_body)
# print("res_dict : ",res_dict)