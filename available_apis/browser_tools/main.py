import os
from typing import Tuple, Any, List
import re
import sqlite3

from langchain_core.outputs import LLMResult
# import ray
# ray.init()

from datasets import load_dataset

from rich import print as pp
from rich.console import Console
from rich.table import Table
from rich import box

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_openai import AzureChatOpenAI
from langchain_community.cache import SQLiteCache
from langchain_core.callbacks import BaseCallbackHandler

from autogen.code_utils import execute_code
import autogen
from autogen.agentchat.contrib.society_of_mind_agent import SocietyOfMindAgent

import asyncio

import time

from available_apis.browser_tools.browser_utils import SimpleTextBrowser

MODEL='gpt-4o'
# MODEL='gpt-4o-2024-08-06'
# MODEL='gpt-4o-2024-05-13'
DATA_NAME = '2023_level1'
SPLIT = 'validation'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_BASE = os.getenv('OPENAI_API_BASE')
BING_API_KEY = os.getenv('BING_API_KEY')

class LLMCallbackHandler(BaseCallbackHandler):

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        print(f"LLM response: {response}")

class Answer(BaseModel):
    reason: str = Field(description="Step by step reasoning")
    answer: str = Field(description="The answer to the question")

class StepNote(BaseModel):
    snippets: List[str] = Field(description="The snippets may use to answer the question, each snippet should less than 1000 characters")
    plan: str = Field(description="Plan for the next step")

class ToolChoice(BaseModel):
    reason: str = Field(description="Step by step reasoning")
    tool: str = Field(description="The tool to use")
    tool_args: dict = Field(description="The arguments to pass to the tool")

class ImproveCode(BaseModel):
    reason: str = Field(description="Step by step reasoning on how to improve the code")
    improved_code: str = Field(description="The improved code")

with open("/Users/aarjun1/Documents/Arjun/Princeton_Work/newCode/interpreter-translator-rapid_apis_GAIA_Simple/available_apis/browser_tools/prompts/format_answer.txt") as f:
    FORMAT_ANSWER_PROMPT = ChatPromptTemplate.from_template(f.read())

with open('/Users/aarjun1/Documents/Arjun/Princeton_Work/newCode/interpreter-translator-rapid_apis_GAIA_Simple/available_apis/browser_tools/prompts/choose_tool.txt') as f:
    CHOOSE_TOOL_PROMPT_TEMPLATE = f.read()

with open('/Users/aarjun1/Documents/Arjun/Princeton_Work/newCode/interpreter-translator-rapid_apis_report/available_apis/browser_tools/prompts/choose_tool_report.txt') as f:
    CHOOSE_TOOL_REPORT_PROMPT_TEMPLATE = f.read()

with open('/Users/aarjun1/Documents/Arjun/Princeton_Work/newCode/interpreter-translator-rapid_apis_GAIA_Simple/available_apis/browser_tools/prompts/summarize_step.txt') as f:
    SUMMARIZE_STEP_PROMPT_TEMPLATE = ChatPromptTemplate.from_template(f.read())

with open('/Users/aarjun1/Documents/Arjun/Princeton_Work/newCode/interpreter-translator-rapid_apis_GAIA_Simple/available_apis/browser_tools/prompts/improve_code.txt') as f:
    IMPROVE_CODE_PROMPT_TEMPLATE = f.read()

# @ray.remote
class Sibyl:
    def __init__(self, interpreter_report_bool=False):
        cache = SQLiteCache("llm_cache.sqlite")
        # self.llm = AzureChatOpenAI(azure_deployment=MODEL, api_version="2024-04-01-preview", temperature=0, streaming=False, max_retries=5, cache=cache, timeout = 350)
        # self.llm_without_cache = AzureChatOpenAI(azure_deployment=MODEL, api_version="2024-04-01-preview", temperature=0.1, streaming=False, max_retries=5, timeout = 350)
        self.llm = ChatOpenAI(model=MODEL, temperature=0, streaming=False, max_retries=5, api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE, cache=cache, timeout = 350)
        self.llm_without_cache = ChatOpenAI(model=MODEL, temperature=0.1, streaming=False, max_retries=5, api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE, timeout = 350)
        self.format_answer_chain = FORMAT_ANSWER_PROMPT | self.llm | StrOutputParser()

        self.tool_choice_output_parser = JsonOutputParser(pydantic_object=ToolChoice)

        if interpreter_report_bool:
            choose_tool_prompt = PromptTemplate(
                template=CHOOSE_TOOL_REPORT_PROMPT_TEMPLATE, 
                input_variables=['steps', 'question'], 
                partial_variables={"format_instructions": self.tool_choice_output_parser.get_format_instructions()}
            )
        else:
            choose_tool_prompt = PromptTemplate(
                template=CHOOSE_TOOL_PROMPT_TEMPLATE, 
                input_variables=['steps', 'question'], 
                partial_variables={"format_instructions": self.tool_choice_output_parser.get_format_instructions()}
            )

        self.choose_tool_chain = choose_tool_prompt | self.llm | self.tool_choice_output_parser
        self.choose_tool_chain_without_cache = choose_tool_prompt | self.llm_without_cache | self.tool_choice_output_parser

        self.improve_code_output_parser = JsonOutputParser(pydantic_object=ImproveCode)
        improve_code_prompt = PromptTemplate(
            template=IMPROVE_CODE_PROMPT_TEMPLATE, 
            input_variables=['steps', 'question', 'code'],
            partial_variables={"format_instructions": self.improve_code_output_parser.get_format_instructions()}
        )
        self.improve_code_chain = improve_code_prompt | self.llm | self.improve_code_output_parser
        self.improve_code_chain_without_cache = improve_code_prompt | self.llm_without_cache | self.improve_code_output_parser

        self.summarize_tool_chain = SUMMARIZE_STEP_PROMPT_TEMPLATE | self.llm | StrOutputParser()

        browser_config={
            "bing_api_key": BING_API_KEY,
            "viewport_size": 1024 * 16,
            "downloads_folder": "coding",
            "request_kwargs": {
                "headers": {"User-Agent":  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"},
            },
        }
        self.browser = SimpleTextBrowser(**browser_config)
        self.llm_callback_handler = LLMCallbackHandler()

        if interpreter_report_bool:
            agent1 = autogen.ConversableAgent(
                name="Actor",
                system_message='''You are a helpful assistant.  When answering a question, you must explain your thought process step by step before answering the question. When others make suggestions about your answers, think carefully about whether or not to adopt the opinions of others.
                For your context we are writing a very comprehensive and detailed report on the above-mentioned query. To achieve this, we must systematically define the report’s sections and their subsections so that we can produce a well-structured, high-quality document.
                Your task is to identify the relevant sections and subsections to be explored for writing a thorough, cohesive report. Also, please specify where plots can be integrated within the relevant subsections by noting them in brackets (e.g., "(visualization could be integrated here)") rather than creating separate subsections solely for visuals. Strictly do not create separate sections or subsections dedicated entirely to visualization. Only python plot based visual elements can be included and must be mentioned parenthetically in the narrative of an existing subsection rather than forming a distinct subsection or section on their own. Additionally, for any mathematical aspects or concepts, ensure they are integrated directly into the relevant sections and subsections rather than creating separate sections or subsections solely for mathematical aspects.
                Do not leave all the plots for the final section. Instead, distribute them throughout the report in different, relevant sections. Limit the use of visual data to 3–5 sections in total.
                Aim to provide 15 to 20 sections in the report. Each section should have between 1 and 5 subsections. If the topic is technical, include more technical details rather than being generic. Whenever applicable, try to include mathematical concepts and equations—particularly in areas like engineering, finance, computer science, or machine learning—to elucidate technical ideas. Remember, however, that the final report is intended for a broad audience, so present the technical content in an accessible manner.
                In the Introduction, skip the objectives of the report, as well as any scope or methodology details. Also, omit the Conclusion, Appendices, and References section strictly always, as they will be handled separately layer. Ensure that your sections and subsections are not repetitive and that you take care to avoid overlapping content. Make the descriptions of each section and subsection extensive and detailed to prevent redundancy or identical information appearing in multiple parts of the report. Additionally, refrain from creating sections or subsections that simply compile information from previous sections; another agent will handle that task later.
                If you are unable to solve the question, make a well-informed EDUCATED GUESS based on the information we have provided.  DO NOT OUTPUT 'I don't know', 'Unable to determine', etc.''',
                # llm_config={"config_list": [{"model": MODEL, "api_type": "azure", "api_version": "2024-04-01-preview", "temperature": 0.1, "api_key": OPENAI_API_KEY, "base_url": OPENAI_API_BASE}]},
                llm_config={"config_list": [{"model": MODEL, "temperature": 0.1, "api_key": OPENAI_API_KEY, "base_url": OPENAI_API_BASE}]},
                is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
            )
        else:
            agent1 = autogen.ConversableAgent(
                name="Actor",
                system_message='''You are a helpful assistant.  When answering a question, you must explain your thought process step by step before answering the question. When others make suggestions about your answers, think carefully about whether or not to adopt the opinions of others.
                For your context we are writing section or sub-section of a report so please provide a detailed response that accumulates enough information for a portion of the report. Keep it verbose but non repetetive please.
                If the topic is technical then try to add more technical and mathematical details like equations rather than being generic.
                If you are unable to solve the question, make a well-informed EDUCATED GUESS based on the information we have provided.  DO NOT OUTPUT 'I don't know', 'Unable to determine', etc.''',
                # llm_config={"config_list": [{"model": MODEL, "api_type": "azure", "api_version": "2024-04-01-preview", "temperature": 0.1, "api_key": OPENAI_API_KEY, "base_url": OPENAI_API_BASE}]},
                llm_config={"config_list": [{"model": MODEL, "temperature": 0.1, "api_key": OPENAI_API_KEY, "base_url": OPENAI_API_BASE}]},
                is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
            )

        if interpreter_report_bool:
            agent2 = autogen.ConversableAgent(
                name="Critic",
                system_message='''You are a helpful assistant.You want to help others spot logical or intellectual errors. When and only when you can't find a logical flaw in the other person's reasoning, you should say "TERMINATE" to end the conversation.
                For your context we are writing a very comprehensive and detailed report on the above-mentioned query. To achieve this, we must systematically define the report’s sections and their subsections so that we can produce a well-structured, high-quality document.
                Your task is to identify the relevant sections and subsections to be explored for writing a thorough, cohesive report. Also, please specify where plots can be integrated within the relevant subsections by noting them in brackets (e.g., "(visualization could be integrated here)") rather than creating separate subsections solely for visuals. Strictly do not create separate sections or subsections dedicated entirely to visualization. Only python plot based visual elements can be included and must be mentioned parenthetically in the narrative of an existing subsection rather than forming a distinct subsection or section on their own. Additionally, for any mathematical aspects or concepts, ensure they are integrated directly into the relevant sections and subsections rather than creating separate sections or subsections solely for mathematical aspects.
                Do not leave all the plots for the final section. Instead, distribute them throughout the report in different, relevant sections. Limit the use of visual data to 3–5 sections in total.
                Aim to provide 15 to 20 sections in the report. Each section should have between 1 and 5 subsections. If the topic is technical, include more technical details rather than being generic. Whenever applicable, try to include mathematical concepts and equations—particularly in areas like engineering, finance, computer science, or machine learning—to elucidate technical ideas. Remember, however, that the final report is intended for a broad audience, so present the technical content in an accessible manner.
                In the Introduction, skip the objectives of the report, as well as any scope or methodology details. Also, omit the Conclusion, Appendices, and References section strictly always, as they will be handled separately layer. Ensure that your sections and subsections are not repetitive and that you take care to avoid overlapping content. Make the descriptions of each section and subsection extensive and detailed to prevent redundancy or identical information appearing in multiple parts of the report. Additionally, refrain from creating sections or subsections that simply compile information from previous sections; another agent will handle that task later.''',
                # llm_config={"config_list": [{"model": MODEL, "api_type": "azure", "api_version": "2024-04-01-preview", "temperature": 0, "api_key": AZURE_OPENAI_API_KEY, "base_url": AZURE_OPENAI_ENDPOINT}]},
                llm_config={"config_list": [{"model": MODEL, "temperature": 0, "api_key": OPENAI_API_KEY, "base_url": OPENAI_API_BASE}]},
            )
        else:
            agent2 = autogen.ConversableAgent(
                name="Critic",
                system_message='''You are a helpful assistant.You want to help others spot logical or intellectual errors. When and only when you can't find a logical flaw in the other person's reasoning, you should say "TERMINATE" to end the conversation.
                For your context we are writing section or sub-section of a report so please provide a detailed response that accumulates enough information for a portion of the report. Keep it verbose but non repetetive please.
                If the topic is technical then try to add more technical and mathematical details like equations rather than being generic.''',
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
            # llm_config={"config_list": [{"model": MODEL, "api_type": "azure", "api_version": "2024-04-01-preview", "temperature": 0.0, "api_key": OPENAI_API_KEY, "base_url": AZURE_OPENAI_ENDPOINT}]},
            llm_config={"config_list": [{"model": MODEL, "temperature": 0.0, "api_key": OPENAI_API_KEY, "base_url": OPENAI_API_BASE}]},
        )

        self.society_of_mind_agent = SocietyOfMindAgent(
            "society_of_mind",
            chat_manager=manager,
            # llm_config={"timeout": 350, "config_list": [{"model": MODEL, "api_type": "azure", "api_version": "2024-04-01-preview", "temperature": 0.0, "api_key": OPENAI_API_KEY, "base_url": AZURE_OPENAI_ENDPOINT}]}
            llm_config={"timeout": 350, "config_list": [{"model": MODEL, "temperature": 0.0, "api_key": OPENAI_API_KEY, "base_url": OPENAI_API_BASE}]}
        )

        self.user_proxy = autogen.UserProxyAgent(
            "user_proxy",
            human_input_mode="NEVER",
            code_execution_config=False,
            default_auto_reply="",
            is_termination_msg=lambda x: True,
        )

        self.interpreter_report_bool = interpreter_report_bool

    def browser_state(self) -> Tuple[str, str]:
        header = f"Address: {self.browser.address}\n"
        if self.browser.page_title is not None:
            header += f"Title: {self.browser.page_title}\n"

        current_page = self.browser.viewport_current_page
        total_pages = len(self.browser.viewport_pages)

        header += f"Viewport position: Showing page {current_page+1} of {total_pages}.\n"
        return (header, self.browser.viewport)
    
    def informational_web_search(self, query: str) -> str:
        self.browser.visit_page(f"bing: {query}")
        header, content = self.browser_state()
        return header.strip() + "\n=======================\n" + content
    
    def navigational_web_search(self, query: str) -> str:
        self.browser.visit_page(f"bing: {query}")
        # Extract the first linl
        m = re.search(r"\[.*?\]\((http.*?)\)", self.browser.page_content)
        if m:
            self.browser.visit_page(m.group(1))

        # Return where we ended up
        header, content = self.browser_state()
        return header.strip() + "\n=======================\n" + content

    def visit_page(self, url: str) -> str:
        self.browser.visit_page(url)
        header, content = self.browser_state()
        return header.strip() + "\n=======================\n" + content

    def page_up(self) -> str:
        self.browser.page_up()
        header, content = self.browser_state()
        return header.strip() + "\n=======================\n" + content

    def page_down(self) -> str:
        self.browser.page_down()
        header, content = self.browser_state()
        return header.strip() + "\n=======================\n" + content

    def download_file(self, url: str) -> str:
        self.browser.visit_page(url)
        header, content = self.browser_state()
        return header.strip() + "\n=======================\n" + content

    def find_on_page_ctrl_f(self, search_string: str) -> str:
        find_result = self.browser.find_on_page(search_string)
        header, content = self.browser_state()

        if find_result is None:
            return (
                header.strip()
                + "\n=======================\nThe search string '"
                + search_string
                + "' was not found on this page."
            )
        else:
            return header.strip() + "\n=======================\n" + content

    def find_next(self) -> str:
        find_result = self.browser.find_next()
        header, content = self.browser_state()

        if find_result is None:
            return header.strip() + "\n=======================\nThe search string was not found on this page."
        else:
            return header.strip() + "\n=======================\n" + content
        
    def computer_terminal(self, code: str) -> str:
        status_code, stdout, _ = execute_code(code, work_dir='coding', use_docker=False, timeout=20)
        return {
            "status_code": status_code,
            "stdout": stdout,
        }

    def ask(self, raw_question: str, attachment_name: str = None) -> str:
        row = None 

        if row is not None:
            print(f"Cache hit for question: {raw_question}")
            return row[0]
        else:
            print(f"Cache miss for question: {raw_question}")

        steps = []

        if attachment_name is not None and attachment_name.strip() != "":
            question = f"{raw_question}\nAttachment: file:///Users/long/workspace/GAIA/2023/{SPLIT}/{attachment_name}"
        else:
            question = raw_question
        pp(f"Question: {question}")

        for _ in range(20):
            has_error = False
            for _ in range(30):
                time.sleep(4)
                # await asyncio.sleep(0.5)
                try:
                    if has_error:
                        tool_choice = self.choose_tool_chain_without_cache.invoke({'question': question, 'steps': '\n\n'.join(steps)})
                    else:
                        tool_choice = self.choose_tool_chain.invoke({'question': question, 'steps': '\n\n'.join(steps)})
                    if tool_choice['tool'] == 'computer_terminal' and tool_choice['tool_args'].get('code', '') == '':
                        has_error = True
                        continue
                    elif tool_choice['tool'] not in ['informational_web_search', 'navigational_web_search', 'visit_page', 'page_up', 'page_down', 'download_file', 'find_on_page_ctrl_f', 'find_next', 'computer_terminal', 'None']:
                        has_error = True
                        continue
                    else:
                            break
                except Exception as e:
                    print(f"Error: {e}")
                    has_error = True
                    continue
            tool = tool_choice['tool']
            args = tool_choice['tool_args']
            pp(f"Tool: {tool}, Args: {args}")
            if tool == "informational_web_search":
                tool_result = self.informational_web_search(**args)
            elif tool == "navigational_web_search":
                tool_result = self.navigational_web_search(**args)
            elif tool == "visit_page":
                tool_result = self.visit_page(**args)
            elif tool == "page_up":
                tool_result = self.page_up()
            elif tool == "page_down":
                tool_result = self.page_down()
            elif tool == "download_file":
                tool_result = self.download_file(**args)
            elif tool == "find_on_page_ctrl_f":
                tool_result = self.find_on_page_ctrl_f(**args)
            elif tool == "find_next":
                tool_result = self.find_next()
            elif tool == 'computer_terminal':
                improve_error = False
                for _ in range(10):
                    try:
                        origin_code = args['code']
                        if improve_error:
                            improved_code = self.improve_code_chain_without_cache.invoke({'question': question, 'steps': '\n\n'.join(steps), 'code': origin_code})['improved_code']
                        else:
                            improved_code = self.improve_code_chain.invoke({'question': question, 'steps': '\n\n'.join(steps), 'code': origin_code})['improved_code']
                        tool_result = self.computer_terminal(improved_code)
                        break
                    except Exception as e:
                        print(f"Error: {e}")
                        improve_error = True
                        continue
            elif tool == 'None':
                tool_result = None
            else:
                print(f"Unknown tool: {tool}")
                tool_result = None
            
            if tool == 'None':
                print(f"No tool chosen, break")
                break

            time.sleep(4)
            step_note = self.summarize_tool_chain.invoke({'question': question, 'steps': '\n\n'.join(steps), 'tool_result': tool_result, 'tool': tool, 'args': args})
            print(f"Step note: \n{step_note}")
            steps.append(f"Step:{len(steps)+1}\nTool: {tool}, Args: {args}\n{step_note}\n\n")

        if len(steps) == 0:
            if self.interpreter_report_bool:
                answer = self.user_proxy.initiate_chat(
                    self.society_of_mind_agent, 
                    message = f"""{question}
                    We are writing a very comprehensive and detailed report on the above-mentioned query. To achieve this, we must systematically define the report’s sections and their subsections so that we can produce a well-structured, high-quality document.
                    Your task is to identify the relevant sections and subsections to be explored for writing a thorough, cohesive report. Also, please specify where plots can be integrated within the relevant subsections by noting them in brackets (e.g., "(visualization could be integrated here)") rather than creating separate subsections solely for visuals. Strictly do not create separate sections or subsections dedicated entirely to visualization. Only python plot based visual elements can be included and must be mentioned parenthetically in the narrative of an existing subsection rather than forming a distinct subsection or section on their own. Additionally, for any mathematical aspects or concepts, ensure they are integrated directly into the relevant sections and subsections rather than creating separate sections or subsections solely for mathematical aspects.
                    Do not leave all the plots for the final section. Instead, distribute them throughout the report in different, relevant sections. Limit the use of visual data to 3–5 sections in total.
                    Aim to provide 15 to 20 sections in the report. Each section should have between 1 and 5 subsections. If the topic is technical, include more technical details rather than being generic. Whenever applicable, try to include mathematical concepts and equations—particularly in areas like engineering, finance, computer science, or machine learning—to elucidate technical ideas. Remember, however, that the final report is intended for a broad audience, so present the technical content in an accessible manner.
                    In the Introduction, skip the objectives of the report, as well as any scope or methodology details. Also, omit the Conclusion, Appendices, and References section strictly always, as they will be handled separately layer. Ensure that your sections and subsections are not repetitive and that you take care to avoid overlapping content. Make the descriptions of each section and subsection extensive and detailed to prevent redundancy or identical information appearing in multiple parts of the report. Additionally, refrain from creating sections or subsections that simply compile information from previous sections; another agent will handle that task later.
                    DO NOT OUTPUT “I don’t know” or “Unable to determine,” etc.""").summary
                
            else:
                answer = self.user_proxy.initiate_chat(
                    self.society_of_mind_agent, 
    #                 message=f"""{question}\nIf you are unable to solve the question or if this is a reasoning or straightforward question which does not need browser tools, then please think about the query and make a well-informed EDUCATED GUESS based on the information provided in the question, including your reasoning. If the topic is technical then try to add more technical details rather than being generic, and if applicable it is strongly recommended to explain engineering, finance, computer science or machine learning related things using mathematical aspects and equations to explain the technical concepts please (but remember that the report is intended towards a wider audience and not technical or mathematical experts, so keep things easy to understand as well). Keep it verbose please.
    # DO NOT OUTPUT 'I don't know', 'Unable to determine', etc. If the query is related to collecting information for making plots, then is the exception where you can say 'I don't know', 'Unable to determine' to avoid making wrong plots.""").summary
                       message=f"""{question}\nIf you are unable to solve the question or if this is a reasoning or straightforward question which does not need browser tools, then please think about the query and make a well-informed EDUCATED GUESS based on the information provided in the question, including your reasoning. If the topic is technical then try to add more technical and mathematical details like equations rather than being generic. Keep it verbose but non repetetive please.
    DO NOT OUTPUT 'I don't know', 'Unable to determine', etc. If the query is related to collecting information for making plots, then is the exception where you can say 'I don't know', 'Unable to determine' to avoid making wrong plots.""").summary
        else:
            steps_prompt = '\n'.join(steps)
            if self.interpreter_report_bool:
                answer = self.user_proxy.initiate_chat(
                    self.society_of_mind_agent, 
                    message=f"""{question}\nTo find the appropriate sections and sub-sections of a report on the given query, I did the following:
    {steps_prompt}

                    Referring to the information I have obtained (which may not be accurate), what do you think should be the most appropriate sections and subsections for the report?
                    We are writing a very comprehensive and detailed report on the above-mentioned query. To achieve this, we must systematically define the report’s sections and their subsections so that we can produce a well-structured, high-quality document.
                    Your task is to identify the relevant sections and subsections to be explored for writing a thorough, cohesive report. Also, please specify where plots can be integrated within the relevant subsections by noting them in brackets (e.g., "(visualization could be integrated here)") rather than creating separate subsections solely for visuals. Strictly do not create separate sections or subsections dedicated entirely to visualization. Only python plot based visual elements can be included and must be mentioned parenthetically in the narrative of an existing subsection rather than forming a distinct subsection or section on their own. Additionally, for any mathematical aspects or concepts, ensure they are integrated directly into the relevant sections and subsections rather than creating separate sections or subsections solely for mathematical aspects.
                    Do not leave all the plots for the final section. Instead, distribute them throughout the report in different, relevant sections. Limit the use of visual data to 3–5 sections in total.
                    Aim to provide 15 to 20 sections in the report. Each section should have between 1 and 5 subsections. If the topic is technical, include more technical details rather than being generic. Whenever applicable, try to include mathematical concepts and equations—particularly in areas like engineering, finance, computer science, or machine learning—to elucidate technical ideas. Remember, however, that the final report is intended for a broad audience, so present the technical content in an accessible manner.
                    In the Introduction, skip the objectives of the report, as well as any scope or methodology details. Also, omit the Conclusion, Appendices, and References section strictly always, as they will be handled separately layer. Ensure that your sections and subsections are not repetitive and that you take care to avoid overlapping content. Make the descriptions of each section and subsection extensive and detailed to prevent redundancy or identical information appearing in multiple parts of the report. Additionally, refrain from creating sections or subsections that simply compile information from previous sections; another agent will handle that task later.
                    DO NOT OUTPUT “I don’t know” or “Unable to determine,” etc.""").summary
                
            else:
                answer = self.user_proxy.initiate_chat(
                    self.society_of_mind_agent, 
                    message=f"""{question}\nTo answer the above question, I did the following:
    {steps_prompt}

    Referring to the information I have obtained (which may not be accurate), what do you think is the answer to the question? Please provide a detailed response that accumulates enough information for a portion of the report. Keep it verbose but non repetetive please.
    If you are unable to solve the question, please think about the query and make a well-informed EDUCATED GUESS based on the information we have provided, including your reasoning. If the topic is technical then try to add more technical and mathematical details like equations rather than being generic.
    DO NOT OUTPUT 'I don't know', 'Unable to determine', etc. If the query is related to collecting information for making plots, then is the exception where you can say 'I don't know', 'Unable to determine' to avoid making wrong plots. Lastly please compile the references (websites, papers, etc) and their specific links if available, used in the answer generated at the end, and simply list them out as References:""").summary

        return answer
    

############################
def browser_tools_function(dict_body, interpreter_report_bool = False):
    response_dict = {}

    if "query" not in dict_body:
        response_dict["status_code"] = 400
        response_dict["text"] = "Missing required parameters query"
        return response_dict
    
    query = dict_body["query"]
    
    sybil_obj = Sibyl(interpreter_report_bool = interpreter_report_bool)

    answer = sybil_obj.ask(query)

    response_dict["status_code"] = 200
    response_dict["text"] = answer

    # print("original sybil answerrrr: ",answer)

    return response_dict


# report check
# dict_body = {"query": "Please provide what sections/subsections should be kept for a detailed and comprehensive report being written on the topic: Analyze how the increased use of renewable energy sources like solar and wind power has affected carbon emission levels worldwide over the past decade."}
# res_dict = browser_tools_function(dict_body, True)
# print("res_dict : ",res_dict)