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
import base64

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_openai import AzureChatOpenAI
from langchain_community.cache import SQLiteCache
from langchain_core.callbacks import BaseCallbackHandler

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

client = OpenAI()

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

with open('/Users/aarjun1/Documents/Arjun/Princeton_Work/newCode/interpreter-translator-rapid_apis_GAIA_Simple/available_apis/browser_tools/prompts/summarize_step.txt') as f:
    SUMMARIZE_STEP_PROMPT_TEMPLATE = ChatPromptTemplate.from_template(f.read())

with open('/Users/aarjun1/Documents/Arjun/Princeton_Work/newCode/interpreter-translator-rapid_apis_GAIA_Simple/available_apis/browser_tools/prompts/improve_code.txt') as f:
    IMPROVE_CODE_PROMPT_TEMPLATE = f.read()

# @ray.remote
class Sibyl:
    def __init__(self):
        cache = SQLiteCache("llm_cache.sqlite")
        # self.llm = AzureChatOpenAI(azure_deployment=MODEL, api_version="2024-04-01-preview", temperature=0, streaming=False, max_retries=5, cache=cache)
        # self.llm_without_cache = AzureChatOpenAI(azure_deployment=MODEL, api_version="2024-04-01-preview", temperature=0.1, streaming=False, max_retries=5)
        self.llm = ChatOpenAI(model=MODEL, temperature=0, streaming=False, max_retries=5, api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE, cache=cache, timeout = 350)
        self.llm_without_cache = ChatOpenAI(model=MODEL, temperature=0.1, streaming=False, max_retries=5, api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE, timeout = 350)
        self.format_answer_chain = FORMAT_ANSWER_PROMPT | self.llm | StrOutputParser()

        self.tool_choice_output_parser = JsonOutputParser(pydantic_object=ToolChoice)
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
        
    def vision_qa(self, url, query):
        if 'file://' in url:
            url = url[7:]
        if 'GAIA' in url:
            with open(url, "rb") as image_file:
                encoded_url = base64.b64encode(image_file.read()).decode('utf-8')
            url = f"data:image/jpeg;base64,{encoded_url}"
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Please provide an answer after analyzing the image for this specific query {query}"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": url,
                                },
                            },
                        ],
                    }
                ],
                max_tokens=300,
            )

            return response.choices[0].message.content
        except Exception as e:
            return "Due to invalid url, the image was not able to be analysed"

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
                try:
                    if has_error:
                        tool_choice = self.choose_tool_chain_without_cache.invoke({'question': question, 'steps': '\n\n'.join(steps)})
                    else:
                        tool_choice = self.choose_tool_chain.invoke({'question': question, 'steps': '\n\n'.join(steps)})
                    if tool_choice['tool'] == 'computer_terminal' and tool_choice['tool_args'].get('code', '') == '':
                        has_error = True
                        continue
                    elif tool_choice['tool'] not in ['informational_web_search', 'navigational_web_search', 'visit_page', 'page_up', 'page_down', 'download_file', 'find_on_page_ctrl_f', 'find_next', 'computer_terminal', 'vision_qa', 'None']:
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
            elif tool == "vision_qa":
                tool_result = self.vision_qa(**args)
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

            step_note = self.summarize_tool_chain.invoke({'question': question, 'steps': '\n\n'.join(steps), 'tool_result': tool_result, 'tool': tool, 'args': args})
            print(f"Step note: \n{step_note}")
            steps.append(f"Step:{len(steps)+1}\nTool: {tool}, Args: {args}\n{step_note}\n\n")

        if len(steps) == 0:
            answer = self.user_proxy.initiate_chat(
                self.society_of_mind_agent, 
                message=f"""{question}\nIf you are unable to solve the question, make a well-informed EDUCATED GUESS based on the information we have provided.
 DO NOT OUTPUT 'I don't know', 'Unable to determine', etc.""").summary
        else:
            steps_prompt = '\n'.join(steps)
            answer = self.user_proxy.initiate_chat(
                self.society_of_mind_agent, 
                message=f"""{question}\nTo answer the above question, I did the following:
{steps_prompt}

Referring to the information I have obtained (which may not be accurate), what do you think is the answer to the question?
If you are unable to solve the question, make a well-informed EDUCATED GUESS based on the information we have provided.
 DO NOT OUTPUT 'I don't know', 'Unable to determine', etc.""").summary
        # formatted_answer = self.format_answer_chain.invoke({'question': question, 'answer': answer})#.answer

        return answer
    

# Reasoning Agent

class ReasoningAgent:
    def __init__(self):
        cache = SQLiteCache("llm_cache.sqlite")
        # self.llm = AzureChatOpenAI(azure_deployment=MODEL, api_version="2024-04-01-preview", temperature=0, streaming=False, max_retries=5, cache=cache)
        # self.llm_without_cache = AzureChatOpenAI(azure_deployment=MODEL, api_version="2024-04-01-preview", temperature=0.1, streaming=False, max_retries=5)
        self.llm = ChatOpenAI(model=MODEL, temperature=0, streaming=False, max_retries=5, api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE, cache=cache, timeout = 350)
        self.llm_without_cache = ChatOpenAI(model=MODEL, temperature=0.1, streaming=False, max_retries=5, api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE, timeout = 350)
        self.format_answer_chain = FORMAT_ANSWER_PROMPT | self.llm | StrOutputParser()


        self.summarize_tool_chain = SUMMARIZE_STEP_PROMPT_TEMPLATE | self.llm | StrOutputParser()

        self.llm_callback_handler = LLMCallbackHandler()

        agent1 = autogen.ConversableAgent(
            name="Actor",
            system_message='''You are a helpful assistant.  When answering a question, you must explain your thought process step by step before answering the question. When others make suggestions about your answers, think carefully about whether or not to adopt the opinions of others.
            For your context, you have to enact as a reasoning agent and find out an answer for the reasoning question through a deep thought process.
            If you are unable to solve the question, make a well-informed EDUCATED GUESS based on the information we have provided.  DO NOT OUTPUT 'I don't know', 'Unable to determine', etc.''',
            # llm_config={"config_list": [{"model": MODEL, "api_type": "azure", "api_version": "2024-04-01-preview", "temperature": 0.1, "api_key": AZURE_OPENAI_API_KEY, "base_url": AZURE_OPENAI_ENDPOINT}]},
            llm_config={"config_list": [{"model": MODEL, "temperature": 0.1, "api_key": OPENAI_API_KEY, "base_url": OPENAI_API_BASE}]},
            is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
        )

        agent2 = autogen.ConversableAgent(
            name="Critic",
            system_message='''You are a helpful assistant.You want to help others spot logical or intellectual errors. When and only when you can't find a logical flaw in the other person's reasoning, you should say "TERMINATE" to end the conversation.
            For your context, you have to enact as a reasoning agent and find out an answer for the reasoning question through a deep thought process.''',
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

    def ask(self, raw_question: str) -> str:
        row = None 

        if row is not None:
            print(f"Cache hit for question: {raw_question}")
            return row[0]
        else:
            print(f"Cache miss for question: {raw_question}")

        steps = []

        question = raw_question
        pp(f"Question: {question}")


        answer = self.user_proxy.initiate_chat(
            self.society_of_mind_agent, 
            message=f"""{question}\nYou have to make a well-informed answer or an educated guess based on the query that has been provided. For your context, you have to enact as a reasoning agent and find out an answer for the reasoning question through a deep thought process.
             DO NOT OUTPUT 'I don't know', 'Unable to determine', etc.""").summary


        return answer

############################
def browser_tools_function(dict_body):
    response_dict = {}

    if "query" not in dict_body:
        response_dict["status_code"] = 400
        response_dict["text"] = "Missing required parameters query"
        return response_dict
    
    query = dict_body["query"]
    
    sybil_obj = Sibyl()

    answer = sybil_obj.ask(query)

    response_dict["status_code"] = 200
    response_dict["text"] = answer

    # print("original sybil answerrrr: ",answer)

    return response_dict

# # report check
# dict_body = {"query": "What is there in the background and forwground of this image in the url: https://images.pexels.com/photos/346885/pexels-photo-346885.jpeg?cs=srgb&dl=pexels-nurseryart-346885.jpg&fm=jpg"}
# res_dict = browser_tools_function(dict_body)
# print("res_dict : ",res_dict)

#########################################
def reasoning_agent_function(dict_body):
    response_dict = {}

    if "query" not in dict_body:
        response_dict["status_code"] = 400
        response_dict["text"] = "Missing required parameters query"
        return response_dict
    
    query = dict_body["query"]
    
    reasoning_agent_obj = ReasoningAgent()

    answer = reasoning_agent_obj.ask(query)

    response_dict["status_code"] = 200
    response_dict["text"] = answer

    # print("original sybil answerrrr: ",answer)

    return response_dict

# report check
# dict_body = {"query": "There are 12 identical balls, one of which is slightly heavier than the others. You have a balance scale and need to find the heavier ball in just 3 weighings. How can you do it?"}
# res_dict = reasoning_agent_function(dict_body)
# print("res_dict : ",res_dict)