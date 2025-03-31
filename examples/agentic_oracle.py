# Agentic Oracle
# 
# This is both a practical agent which can help you build _other_ agents, and also
# a demonstration of using RAG and tools with your agent.
#
from agentic.common import Agent, AgentRunner
from agentic.tools import RAGTool

# Define our agent, and attach the RAG, plus pre-populate with the Agentic docs.
oracle = Agent(
    name="Agentic Oracle",
    welcome="I can help answer questions about the agentic framework, or help you build new agents.",
    instructions="""
    You are an expert at building agents with the Agentic Framework (https://github.com/supercog-ai/agentic).
    NEVER USE YOUR PRIOR KNOWLEDGE. Always check your knowledge store (via search_knowledge_index)
    to retrieve information before answering questions.
    """,
    tools=[
        RAGTool(
            default_index="oracle",
            index_paths=["./docs/*.md"]
        ),
    ],
)

if __name__ == "__main__":
    AgentRunner(oracle).repl_loop()
