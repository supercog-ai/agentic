import pytest
from agentic.common import Agent
from pydantic import BaseModel, Field
from typing import List
from agentic.agentic_secrets import agentic_secrets
from agentic.models import GPT_4O_MINI, CLAUDE
class MyTestResponseModel(BaseModel):
    response: str
    number: int

class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Query for web search.")

class Queries(BaseModel):
    queries: List[SearchQuery] = Field(
        description="List of search queries.",
    )

@pytest.mark.requires_llm
def test_response_model():
    agent = Agent(
        name="Test Agent",
        instructions="Make a joke about the input, and return a random number",
        model=GPT_4O_MINI,
        result_model=MyTestResponseModel,
    )
    result  = agent.grab_final_result("an old cat")
    assert isinstance(result, MyTestResponseModel)

    agent.set_result_model(Queries)
    result  = agent.grab_final_result("write some search queries to research WWII")
    assert isinstance(result, Queries)

@pytest.mark.requires_llm
def test_claude_response_model():
    if agentic_secrets.get_secret("ANTHROPIC_API_KEY") is None:
        print("Skipping Claude response model test, NO API key")
        return
    
    agent = Agent(
        name="Test Agent",
        instructions="Make a joke about the input, and return a random number",
        model=CLAUDE,
        result_model=MyTestResponseModel,
    )
    result = agent.grab_final_result("an old cat")
    assert isinstance(result, MyTestResponseModel)

    agent.set_result_model(Queries)
    result  = agent.grab_final_result("write some search queries for research WWII")
    assert isinstance(result, Queries)
