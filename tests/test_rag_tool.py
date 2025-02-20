import pytest
from agentic.common import Agent, AgentRunner
from agentic.tools.rag_tool import RAGTool

@pytest.fixture
def rag_agent():
    return Agent(
        name="RAG Test Agent",
        instructions="Use the RAG tools when requested. Always respond with the exact tool output.",
        tools=[RAGTool()],
        model="openai/gpt-4o-mini",
    )

@pytest.fixture
def runner(rag_agent):
    return AgentRunner(rag_agent)

def test_save_content_to_index(runner):
    # Test basic content saving
    url = "https://raw.githubusercontent.com/deepseek-ai/DeepSeek-R1/refs/heads/main/README.md"
    response = runner.turn(f"Save the {url} to index 'pytest_save'")
    assert "Indexed" in response
    assert "pytest_save" in response

def test_list_indexes(runner):
    
    # Test listing indexes
    response = runner.turn("List all knowledge indexes")
    assert "pytest_save" in response

def test_search_knowledge_index(runner):
    
    # Test search
    response = runner.turn("Search for 'deepseek' in index 'pytest_save'")
    assert any("deepseek" in str(item) for item in response)

def test_list_documents(runner):

    response = runner.turn("List documents in index 'pytest_save'")
    assert "readme.md" in str(response).lower()

def test_review_full_document(runner):

    docs = runner.turn("List documents in index 'pytest_save'")
    document_id = next(iter(docs))["document_id"]
    
    # Test full document review
    response = runner.turn(f"Review document {document_id} in index 'pytest_save'")
    assert "deepseek" in response.lower()