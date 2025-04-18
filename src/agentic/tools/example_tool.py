## required package imports should go here
from typing import Callable
import pandas as pd

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry
from agentic.common import RunContext, PauseForInputResult

###
## Register the tool to the tool registry
###

@tool_registry.register(
    name="ExampleTool",
    description="Example tool for demponstrating tool registration",
    dependencies=[],
    config_requirements=[],
)

class ExampleTool(BaseAgenticTool):
    # instance vars for authentication or other configuration
    api_key: str

    # Any initializer parameters should have default values
    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def get_tools(self) -> list[Callable]:
        return [
            self.tool_function_one,
            self.tool_returns_tabluar_data,
            self.sometimes_auth_required,
        ]

    # each function should have a good descriptive name. Make sure names are not too generic.
    # If they are you can prefix with the tool name, like `github_read_file`.
    def tool_function_one(
        self, run_context: RunContext, param1: str, param2: str
    ) -> str:
        """Every function needs a docstring which describes its purpose, inputs and outputs.
        Docstrings should be short, not more than 2 sentences.
        Every function should take the special 'run_context' parameter which provides metadata to the tool.
        """
        pass

    async def tool_returns_tabluar_data(self, query: str) -> pd.DataFrame:
        """Functions can be sync or async. Functions that return records, such as from
        an API call, are encouraged to return a pandas dataframe. Other functions
        can typically return strings or lists of strings."""

        # function logic here

        return pd.DataFrame()

    def sometimes_auth_required(
        self, run_context: RunContext, param1: str
    ) -> str | PauseForInputResult:
        """If a tool requires authentication, the easiest method is to take an API key
        in the constructor. Functions can also request secrets from the RunContext.
        """
        api_key = run_context.get_secret("api_key", self.api_key)

        # If the api key isn't available, the tool can request the agent to pause and
        # ask for it. After the user provides the value, this function will be called again
        # but the value will be present in the run_context.
        if not api_key:
            return PauseForInputResult(
                {"API_KEY_NAME": "Please supply the API_KEY_NAME"}
            )

        # now use the api_key
        return "the result"
