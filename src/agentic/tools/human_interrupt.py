from typing import Callable

from .base import BaseAgenticTool
from agentic.events import PauseForInputResult
from agentic.common import RunContext


class HumanInterruptTool(BaseAgenticTool):
    def __init__(self):
        pass

    def get_tools(self) -> list[Callable]:
        return [self.stop_for_input]

    def stop_for_input(self, request_message: str, run_context: RunContext):
        """ Stop and ask the user for input """
        if run_context.get("input"):
            return run_context.get("input")
        return PauseForInputResult({"input": request_message})
