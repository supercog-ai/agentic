import pytest
from agentic.common import Agent, AgentRunner
from agentic.tools import RAGTool

@pytest.fixture
def rag_agent():
    return Agent(
        name="RAG Test Agent",
        instructions="""You are a testing agent for RAG tools.
        YOUR ONLY JOB IS TO PASS THE RAW TOOL OUTPUT TO THE USER WITHOUT MODIFICATION.
        DO NOT INTERPRET, FORMAT, OR EXPLAIN THE TOOL OUTPUT.
        ALWAYS return the EXACT and COMPLETE tool output in its original format.
        When a tool returns JSON or a list, preserve that exact structure.
        When using the RAG tools, use 'pytest_save' as the index name unless specified otherwise.
        Never wrap outputs in markdown code blocks or quotes.""",
        tools=[RAGTool(default_index="pytest_save")],
        model="openai/gpt-4o-mini",
    )

@pytest.fixture
def runner(rag_agent):
    return AgentRunner(rag_agent)

@pytest.mark.requires_llm
def test_save_content_to_index(runner):
    # Test basic content saving
    url = "https://raw.githubusercontent.com/deepseek-ai/DeepSeek-R1/refs/heads/main/README.md"
    response = runner.turn(f"Save the {url} to index 'pytest_save'")
    assert ("Indexed" in response and "pytest_save" in response) or "README.md" in response

@pytest.mark.requires_llm
def test_search_knowledge_index(runner):
    # Test search
    response = runner.turn("Search for 'deepseek' in index 'pytest_save'")
    # The response should be a list (or serialized list)
    if isinstance(response, str):
        import json
        try:
            response = json.loads(response)
        except:
            # If not JSON, check if the string contains deepseek
            assert "deepseek" in response.lower()
            return
    
    assert any("deepseek" in str(item).lower() for item in response)

@pytest.mark.requires_llm
def test_list_documents(runner):

    response = runner.turn("List documents in index 'pytest_save'")
    assert "readme.md" in str(response).lower()

@pytest.mark.requires_llm
def test_review_full_document(runner):
    response = runner.turn(f"Review document readme.md in index 'pytest_save'")
    assert len(response) > 0  # Just check that we got some content back
