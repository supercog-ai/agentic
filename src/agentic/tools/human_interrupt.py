from typing import Callable

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry
from agentic.events import PauseForInputResult
from agentic.common import ThreadContext

@tool_registry.register(
    name="HumanInterruptTool",
    description="A tool that allows the user to interrupt the agent and provide input.",
    dependencies=[],
    config_requirements=[],
)

class HumanInterruptTool(BaseAgenticTool):
    def __init__(self):
        pass

    def get_tools(self) -> list[Callable]:
        return [self.stop_for_input]

    def stop_for_input(self, request_message: str, thread_context: ThreadContext):
        """ Stop and ask the user for input """
        if thread_context.get("input"):
            return thread_context.get("input")
        return PauseForInputResult({"input": request_message})
