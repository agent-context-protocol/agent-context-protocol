# import asyncio
# from autogen_agentchat.ui import Console
# from autogen_agentchat.teams import RoundRobinGroupChat
# from autogen_ext.models.openai import OpenAIChatCompletionClient
# from langchain_openai import ChatOpenAI
# from autogen_ext.agents.web_surfer import MultimodalWebSurfer
# from autogen_core import CancellationToken
# from autogen_agentchat.messages import TextMessage
# import os



# async def main() -> None:
#     MODEL='gpt-4o-2024-08-06'
#     OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
#     OPENAI_API_BASE = os.getenv('OPENAI_API_BASE')
#     # Define an agent
#     web_surfer_agent = MultimodalWebSurfer(
#         name="MultimodalWebSurfer",
#         model_client=OpenAIChatCompletionClient(model="gpt-4o-2024-08-06"),
#         headless=True  # Run in headless mode without a visible browser window
#     )

#     # # Define a team
#     # agent_team = RoundRobinGroupChat([web_surfer_agent], max_turns=3)

#     # # Run the team and stream messages to the console
#     # stream = agent_team.run_stream(task="Navigate to the AutoGen readme on GitHub.")
#     # await Console(stream)
#     # # Close the browser controlled by the agent
#     # await web_surfer_agent.close()

#     # Define the task for the agent
#     task_message = TextMessage(content="Navigate to the AutoGen readme on GitHub.", source="user")

#     # Send the message to the agent and get the response
#     response = await web_surfer_agent.on_messages(
#         messages=[task_message],
#         cancellation_token=CancellationToken()
#     )

#     # Print the agent's response
#     print(response.chat_message.content)

#     # Close the agent to release resources
#     await web_surfer_agent.close()


# asyncio.run(main())


import asyncio
import os
from autogen_core import CancellationToken
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer

async def main() -> None:
    # Initialize the model client
    model_client = OpenAIChatCompletionClient(model="gpt-4o-2024-08-06")

    # Create the MultimodalWebSurfer agent
    web_surfer_agent = MultimodalWebSurfer(
        name="MultimodalWebSurfer",
        model_client=model_client,
        headless=True  # Set to False to see the browser actions
    )

    # Start the browser session
    await web_surfer_agent._lazy_init()

    # Iterative interaction loop
    try:
        while True:
            user_input = input("Enter your command (or 'exit' to quit): ")
            if user_input.lower() == 'exit':
                break

            # Create a TextMessage with the user's command
            task_message = TextMessage(content=user_input, source="user")

            # Send the message to the agent and get the response
            response = await web_surfer_agent.on_messages(
                messages=[task_message],
                cancellation_token=CancellationToken()
            )

            # Print the agent's response
            print("Agent's response:", response.chat_message.content)

    finally:
        # Close the agent to release resources
        await web_surfer_agent.close()

# Run the main function
asyncio.run(main())