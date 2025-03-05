from agentic.actor_agents import RayFacadeAgent
from pydantic import BaseModel, Field
from typing import List
from agentic.agentic_secrets import agentic_secrets
from agentic.models import CLAUDE
class ResponseModel(BaseModel):
    response: str
    number: int

class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Query for web search.")

class Queries(BaseModel):
    queries: List[SearchQuery] = Field(
        description="List of search queries.",
    )

def test_response_model():
    
    agent = RayFacadeAgent(
        name="Test Agent",
        instructions="Make a joke about the input, and return a random number",
        model="gpt-4o-mini",
        result_model=ResponseModel,
    )
    result  = agent.grab_final_result("an old cat")
    assert isinstance(result, ResponseModel)
    print("GPT: ", result)

    agent.set_result_model(Queries)
    result  = agent.grab_final_result("write some search queries for research WWII")
    assert isinstance(result, Queries)
    print("GPT queries: ", result)

def test_claude_response_model():
    if agentic_secrets.get_secret("ANTHROPIC_API_KEY") is None:
        print("Skipping Claude response model test, NO API key")
        return
    
    agent = RayFacadeAgent(
        name="Test Agent",
        instructions="Make a joke about the input, and return a random number",
        model=CLAUDE,
        result_model=ResponseModel,
    )
    result = agent.grab_final_result("an old cat")
    assert isinstance(result, ResponseModel)
    print("Claude result: ", result)

    agent.set_result_model(Queries)
    result  = agent.grab_final_result("write some search queries for research WWII")
    assert isinstance(result, Queries)
    print("Claude queries: ", result)
