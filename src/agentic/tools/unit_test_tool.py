import asyncio
import os
from typing import Callable

# A dummy tool created just for unit testing

STATE_FILE = "test_state.txt"

class UnitTestingTool():
    def get_tools(self) -> list[Callable]:
        return [
            self.cleanup_state_file,
            self.sleep_for_time,
            self.read_state_file,
            self.test_using_async_call,
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

