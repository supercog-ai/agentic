# mock agent for testing github integration

from agentic.common import Agent, AgentRunner 
from agentic.models import GPT_4O_MINI # model

from dotenv import load_dotenv
import openai
import requests
import os


load_dotenv()  # This loads variables from .env into os.environ
openai.api_key = os.getenv("OPENAI_API_KEY") # api key


# Define the agent
agent = Agent(
    name="Mock PR Summary Agent",

    # Agent instructions
    instructions="""
    You are a helpful mock PR sumary agent to test github integration.
    
    

    """,
    
    model=GPT_4O_MINI, # model
    tools=[],
    memories=[]

)

# basic main function that allows us to run our agent locally in terminal
if __name__ == "__main__":
    AgentRunner(agent).fi