# Basic RAG Agent
# 
#
from agentic.common import Agent, AgentRunner
from agentic.tools import RAGTool

# Define our agent, and attach the RAG Tool, plus pre-populate with some content.
rag_agent = Agent(
    name="My RAG Agent",
    welcome="I can answer question from this web page: https://supercog.ai/blog-posts/how-ai-tools-can-help-your-team-move-faster.",
    instructions="""
    You have a basic knowledge base to answer questions.
    NEVER USE YOUR PRIOR KNOWLEDGE. Always check your knowledge store (via search_knowledge_index)
    to retrieve information before answering questions.
    """,
    tools=[
        RAGTool(
            default_index="test_index",
            index_paths=["https://supercog.ai/blog-posts/how-ai-tools-can-help-your-team-move-faster"]
        ),
    ],
)

if __name__ == "__main__":
    AgentRunner(rag_agent).repl_loop()
