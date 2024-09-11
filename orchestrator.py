import asyncio
from interpreter import InterpreterNode
from main_translator import MainTranslatorNode
from local_translator import LocalTranslatorNode
import json

# class Manager:
#     def __init__(self, workflow, main_translator):
#         # self.queue = asyncio.Queue()
#         # self.lock = asyncio.Lock()
#         self.groups = {}
#         self.translator_list = []
#         for group_id in sorted(workflow.keys()):
#             self.groups[group_id] = {}
#             for instance_id in sorted(workflow[group_id].keys()):
#                 self.groups[group_id][instance_id] = LocalTranslatorNode(instance_id, workflow[group_id][instance_id])
#                 self.translator_list.append(self.groups[group_id][instance_id])
#         self.main_translator = main_translator

#     async def setup_individually(self, local_translator):
#         setup_message = await local_translator.setup()
#         response = await self.query_main_translator(setup_message)
#         return response

#     async def setup(self):
#         await asyncio.gather(*(self.setup_individually(local_translator) for local_translator in self.translator_list))

#     async def query_main_translator(self, query):
#         async with self.main_translator.lock
#             response = await self.main_translator.query(query)
#             return response

#     async def run_group_sequentially(self, group): 
#         for translator in group:
#             await self.run_translator(translator)


class MainOrchestrator:
    def __init__(self):
        self.get_system_prompts()
        self.interpreter = InterpreterNode('interpreter', system_prompt = self.interpreter_system_prompt)
        self.main_translator = MainTranslatorNode('main_translator', self.main_translator_system_prompt)
        self.local_translators = {}

    def get_system_prompts(self):
        # Interpreter system prompt
        with open('prompts/interpreter_system_prompt.txt', 'r') as file:
            self.interpreter_system_prompt = file.read()

        # Main Translator System Prompt
        with open('prompts/main_translator/main_translator_system_prompt.txt', 'r') as file:
            self.main_translator_system_prompt = file.read()
        
        # Local Translator System Prompt
        with open('prompts/local_translator/local_translator_system_prompt.txt', 'r') as file:
            self.local_translator_system_prompt = file.read()

    def run(self, user_query):
        # Send user query to interpreter
        self.interpreter.user_query = user_query

        # Get initial setup from interpreter and send to main translator
        # panels_list = self.interpreter.setup()
        # panels_list = [{'instance_id': 1, 'panel_description': 'Relevant Vacation Destinations', 'request': {'Message_type': 'NEW_PANEL', 'description': "Display a selection of appropriate vacation destinations within India and globally that align with the user's age group and location. Each recommendation should detail the destination's main attractions and the best times to go. This panel might also show travel advisories or restrictions that could affect the user's trip.", 'relevant_apis': [{'Input': 'A query along with relevant response from Perplexity.', 'Output': "If plots are generated, it returns the location where plots are saved and a plot explanation string; otherwise, it returns 'Fail.'", 'Use': 'For queries that can be visualized through graphs or charts. If initial information is insufficient, it triggers a Perplexity search for more data. It can skip plotting if it determines that plotting does not make sense.', 'api_name': 'PlotAgent'}, {'Input': 'The API takes the following input parameters: latitude and longitude (required), hourly and daily weather variables (optional), current_weather (optional), temperature_unit (optional), wind_speed_unit (optional), timeformat (optional), timezone (optional), and past_days (optional).', 'Output': 'The API provides a weather forecast with hourly and daily data. The output includes weather variables such as temperature, humidity, precipitation, wind speed, and more, along with timestamps in the specified format. For current weather conditions, it includes attributes like temperature, wind speed, wind direction, and weather code.', 'Use': 'This API is used to retrieve weather forecasts for a specific location given by latitude and longitude coordinates. It is suitable for applications needing weather data for planning events, monitoring conditions, or integrating weather information into services.', 'api_name': 'Open-Meteo'}, {'Input': 'A simple query that requires searching the web.', 'Output': 'A compiled answer based on web search results.', 'Use': 'As a search engine to retrieve and synthesize information from multiple sources into a single, concise response.', 'api_name': 'Perplexity'}, {'Input': 'A prompt describing an image.', 'Output': 'A location where the image generated based on the input prompt, is saved.', 'Use': 'For generating visually compelling illustrations or images that enhance and complement the response, especially when plots are not appropriate.', 'api_name': 'TextToImage'}, {'Input': "Parameters for querying user details include 'ids', 'filter', and 'site'.", 'Output': 'Returns information about users on the Stack Exchange site, including their reputation, user type, and associated questions and answers.', 'Use': 'Obtain details about users on the Stack Exchange site, which can be useful for user analysis, profile lookups, or understanding user contributions to the site.', 'api_name': 'Stack_Exchange_Users'}]}}, {'instance_id': 2, 'panel_description': 'Vacation Itinerary Planner', 'request': {'Message_type': 'NEW_PANEL', 'description': "Present an interactive vacation planning tool which will allow the user to input their chosen destination, the duration of their vacation, and their preferences in terms of activities or experiences. The tool should then generate a proposed itinerary that includes recommended activities and attractions, places to eat, and accommodation options. The itinerary should also consider the user's professional background and suggest local places related to technology and AI that he could visit.", 'relevant_apis': [{'Input': 'A query along with relevant response from Perplexity.', 'Output': "If plots are generated, it returns the location where plots are saved and a plot explanation string; otherwise, it returns 'Fail.'", 'Use': 'For queries that can be visualized through graphs or charts. If initial information is insufficient, it triggers a Perplexity search for more data. It can skip plotting if it determines that plotting does not make sense.', 'api_name': 'PlotAgent'}, {'Input': 'The API takes the following input parameters: latitude and longitude (required), hourly and daily weather variables (optional), current_weather (optional), temperature_unit (optional), wind_speed_unit (optional), timeformat (optional), timezone (optional), and past_days (optional).', 'Output': 'The API provides a weather forecast with hourly and daily data. The output includes weather variables such as temperature, humidity, precipitation, wind speed, and more, along with timestamps in the specified format. For current weather conditions, it includes attributes like temperature, wind speed, wind direction, and weather code.', 'Use': 'This API is used to retrieve weather forecasts for a specific location given by latitude and longitude coordinates. It is suitable for applications needing weather data for planning events, monitoring conditions, or integrating weather information into services.', 'api_name': 'Open-Meteo'}, {'Input': 'A simple query that requires searching the web.', 'Output': 'A compiled answer based on web search results.', 'Use': 'As a search engine to retrieve and synthesize information from multiple sources into a single, concise response.', 'api_name': 'Perplexity'}, {'Input': 'A prompt describing an image.', 'Output': 'A location where the image generated based on the input prompt, is saved.', 'Use': 'For generating visually compelling illustrations or images that enhance and complement the response, especially when plots are not appropriate.', 'api_name': 'TextToImage'}, {'Input': "Parameters for querying user details include 'ids', 'filter', and 'site'.", 'Output': 'Returns information about users on the Stack Exchange site, including their reputation, user type, and associated questions and answers.', 'Use': 'Obtain details about users on the Stack Exchange site, which can be useful for user analysis, profile lookups, or understanding user contributions to the site.', 'api_name': 'Stack_Exchange_Users'}]}}, {'instance_id': 3, 'panel_description': 'Future Vacation Reminder', 'request': {'Message_type': 'NEW_PANEL', 'description': "Provide an interactive panel to schedule future reminders or alerts for the planning and booking of vacations around the user's calendar events. The alerts should consider not only the user's planned daily standups but also any other meetings or tasks which have not been mentionned yet.", 'relevant_apis': [{'Input': 'The API takes the following input parameters: latitude and longitude (required), hourly and daily weather variables (optional), current_weather (optional), temperature_unit (optional), wind_speed_unit (optional), timeformat (optional), timezone (optional), and past_days (optional).', 'Output': 'The API provides a weather forecast with hourly and daily data. The output includes weather variables such as temperature, humidity, precipitation, wind speed, and more, along with timestamps in the specified format. For current weather conditions, it includes attributes like temperature, wind speed, wind direction, and weather code.', 'Use': 'This API is used to retrieve weather forecasts for a specific location given by latitude and longitude coordinates. It is suitable for applications needing weather data for planning events, monitoring conditions, or integrating weather information into services.', 'api_name': 'Open-Meteo'}, {'Input': 'A query along with relevant response from Perplexity.', 'Output': "If plots are generated, it returns the location where plots are saved and a plot explanation string; otherwise, it returns 'Fail.'", 'Use': 'For queries that can be visualized through graphs or charts. If initial information is insufficient, it triggers a Perplexity search for more data. It can skip plotting if it determines that plotting does not make sense.', 'api_name': 'PlotAgent'}, {'Input': 'A simple query that requires searching the web.', 'Output': 'A compiled answer based on web search results.', 'Use': 'As a search engine to retrieve and synthesize information from multiple sources into a single, concise response.', 'api_name': 'Perplexity'}, {'Input': 'A prompt describing an image.', 'Output': 'A location where the image generated based on the input prompt, is saved.', 'Use': 'For generating visually compelling illustrations or images that enhance and complement the response, especially when plots are not appropriate.', 'api_name': 'TextToImage'}, {'Input': "Parameters for querying user details include 'ids', 'filter', and 'site'.", 'Output': 'Returns information about users on the Stack Exchange site, including their reputation, user type, and associated questions and answers.', 'Use': 'Obtain details about users on the Stack Exchange site, which can be useful for user analysis, profile lookups, or understanding user contributions to the site.', 'api_name': 'Stack_Exchange_Users'}]}}, {'instance_id': 4, 'panel_description': 'Vacation Readings and Resources', 'request': {'Message_type': 'NEW_PANEL', 'description': "Based on the user's bookmarks and recent search history, select relevant reading materials, articles, or learning resources related to AI and coding, which the user may wish to engage with during his vacation. This also could include relevant resources to the user's location, or to the chosen destination.", 'relevant_apis': [{'Input': 'The API takes the following input parameters: latitude and longitude (required), hourly and daily weather variables (optional), current_weather (optional), temperature_unit (optional), wind_speed_unit (optional), timeformat (optional), timezone (optional), and past_days (optional).', 'Output': 'The API provides a weather forecast with hourly and daily data. The output includes weather variables such as temperature, humidity, precipitation, wind speed, and more, along with timestamps in the specified format. For current weather conditions, it includes attributes like temperature, wind speed, wind direction, and weather code.', 'Use': 'This API is used to retrieve weather forecasts for a specific location given by latitude and longitude coordinates. It is suitable for applications needing weather data for planning events, monitoring conditions, or integrating weather information into services.', 'api_name': 'Open-Meteo'}, {'Input': 'A query along with relevant response from Perplexity.', 'Output': "If plots are generated, it returns the location where plots are saved and a plot explanation string; otherwise, it returns 'Fail.'", 'Use': 'For queries that can be visualized through graphs or charts. If initial information is insufficient, it triggers a Perplexity search for more data. It can skip plotting if it determines that plotting does not make sense.', 'api_name': 'PlotAgent'}, {'Input': 'A simple query that requires searching the web.', 'Output': 'A compiled answer based on web search results.', 'Use': 'As a search engine to retrieve and synthesize information from multiple sources into a single, concise response.', 'api_name': 'Perplexity'}, {'Input': 'A prompt describing an image.', 'Output': 'A location where the image generated based on the input prompt, is saved.', 'Use': 'For generating visually compelling illustrations or images that enhance and complement the response, especially when plots are not appropriate.', 'api_name': 'TextToImage'}, {'Input': "Parameters for querying user details include 'ids', 'filter', and 'site'.", 'Output': 'Returns information about users on the Stack Exchange site, including their reputation, user type, and associated questions and answers.', 'Use': 'Obtain details about users on the Stack Exchange site, which can be useful for user analysis, profile lookups, or understanding user contributions to the site.', 'api_name': 'Stack_Exchange_Users'}]}}]
        # message = self.main_translator.setup(user_query, panels_list) 
        with open("workflow.json", "r") as json_file:
            message = json.load(json_file)
        self.local_translators_1 = LocalTranslatorNode(0, message["1"]["1"]["panel_description"], system_prompt = self.local_translator_system_prompt)
        self.local_translators_1.workflow = message["1"]["1"]["steps"]
        self.local_translators_1.build_verify()

        # communication_manager = Manager(workflow)
        # setup_message = group_data_structure.setup()
        # confirmation = self.main_translator.communicate(setup_message)
        # # group_data_structure.recieve_confirmation = 

        # # Main loop
        # while True:
        #     # Process messages between nodes
        #     group_data_structure.run()

        #     # Check if all work is complete
        #     if self.is_work_complete():
        #         break

        # # After completion, we might want to save or analyze the chat histories

if __name__ == "__main__":
    from google_auth_oauthlib.flow import InstalledAppFlow

    orchestrator = MainOrchestrator()
    orchestrator.run("Vacation")
