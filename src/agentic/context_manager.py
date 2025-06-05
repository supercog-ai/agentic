# _ContextManager_ interface defines objects help modify Agent behavior.
# These are the rough equivalents to LangChain callbacks.
#
# They are called "ContextManagers" because managing the LLM context is such a
# common concern. But they can also do query routing and other orchestration operations.
#
# Can be used to implement features like:
#
# - injecting content persistently (every turn) into the context
#   Use 'handle_turn_start' to inject content into the agent.
# - redacting secret values so they aren't seen by  the agent
#   Use 'handle_turn_start' to replace sensitive values with tokens
# - RAG retrieval
#   Use 'handle_turn_start' to retrieve chunks and inject into context
# - Query routing
#   Use 'handle_turn_start' to analyze query and route to different retrievers
#   Route a request to another agent

# - Paging large results
#   Use 'process_tool_result' to wrap a large result in a pager object
#
# Examples:
#
# You want your agent to know what time it is:
#
# class TimeContextManager(ContextManager):
#     def handle_turn_start(self, agent: Agent, prompt: Prompt, thread_context: ThreadContext) -> str:
#         agent.inject_context(f"The current time is {datetime.now()}")
#
# You want to implement Retrieval-augmented generation
#
# class RAGContextManager(ContextManager):
#     def handle_turn_start(self, agent: Agent, prompt: Prompt, thread_context: ThreadContext) -> str:
#         chunks = retrieve_chunks(prompt)
#         for chunk in chunks:
#             agent.inject_context(chunk)
#

from .common import Agent, ThreadContext
from .events import Prompt, TurnEnd, Event

class ContextManager:
    def handle_turn_start(self, agent: Agent, prompt: Prompt, thread_context: ThreadContext) -> Event:
        pass

    def handle_turn_end(self, agent: Agent, turn_end: TurnEnd, thread_context: ThreadContext) -> Event:
        pass

    def handle_tool_start(self, agent: Agent, params: dict, thread_context: ThreadContext) -> str:
        pass

    def handle_tool_result(self, agent: Agent, tool_result: str, thread_context: ThreadContext) -> str:
        pass

