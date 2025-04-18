import asyncio
import os
from typing import Callable

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry
from agentic.common import RunContext

STATE_FILE = "test_state.txt"

@tool_registry.register(
    name="UnitTestingTool",
    description="A dummy tool created just for unit testing",
    dependencies=[],
    config_requirements=[],
)

class UnitTestingTool(BaseAgenticTool):
    def __init__(self, story_log: str="log.txt"):
        self.story_log = story_log

    def get_tools(self) -> list[Callable]:
        return [
            self.cleanup_state_file,
            self.sleep_for_time,
            self.read_state_file,
            self.test_using_async_call,
            self.read_story_log,
            self.sync_function_with_logging,
            self.sync_function_direct_logging,
            self.async_function_with_logging,
        ]

    def sleep_for_time(self, seconds: int):
        """
        Sleep for the given number of seconds
        """
        import time

        time.sleep(seconds)

    def cleanup_state_file(self):
        """
        Remove the state file
        """
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        return "OK"

    def read_state_file(self) -> str:
        """
        Read the contents of the state file
        """
        if not os.path.exists(STATE_FILE):
            return "Error, no state file found"

        with open(STATE_FILE, "r") as f:
            return f.read()

    async def test_using_async_call(self):
        await asyncio.sleep(1)

    async def read_story_log(self) -> str:
        """Reads and returns the story log content."""
        await asyncio.sleep(0.2)
        return self.story_log

    def sync_function_with_logging(self, run_context: RunContext):
        """ A function that logs to the run context. """
        run_context.log("Something interesting happened: ", "thing1", "thing2")
        return "can you see the logs?"

    def sync_function_direct_logging(self, run_context: RunContext):
        """ A function that logs directly via yield. """
        yield run_context.log("Something interesting happened: ", "thing1", "thing2")
        return "I yielded a log message"
    
    async def async_function_with_logging(self, run_context: RunContext):
        """ An async function that logs to the run context. """
        yield run_context.log("ASYNC interesting happened: ", "thing1", "thing2")
        yield "can you see the logs?"
