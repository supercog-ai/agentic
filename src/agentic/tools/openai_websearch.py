import re
from typing import Callable

from openai import OpenAI

from agentic.common import Agent, AgentRunner, ThreadContext
from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import (ConfigRequirement, Dependency,
                                          tool_registry)


@tool_registry.register(
    name="OpenAIWebSearchTool",           # Name of your tool
    description="Tool for searching the web with the OpenAI API",     # Description of what your tool does
    dependencies=[                 # External packages required by your tool
        Dependency(
            name="openai",
            version="1.75.0",
            type="pip",
        ),
    ],
    config_requirements=[          # Configuration settings required by your tool
        ConfigRequirement(
            key="OPENAI_API_KEY",
            description="OpenAI API key",
            required=True,         # Whether this setting is required
        ),
    ],
)

class OpenAIWebSearchTool(BaseAgenticTool):
    """
    Tool to search web using the new openAI 'gpt-4o-mini-search-preview' model. 
    Using this tool will always trigger the model to perform a web search before responding
    to your query.
    """

    def __init__(self):
        pass
    
    def get_tools(self) -> list[Callable]:
        """Return a list of functions that will be exposed to the agent."""
        return [
            self.perform_web_search,
        ]

    async def perform_web_search(self, prompt: str,  thread_context: ThreadContext):
        """
        Function to prompt the model to perform a web search.

        Args:
            prompt: The message to prompt the model with

        Returns:
            The message returned by the model
        """
        client = OpenAI(api_key=thread_context.get_secret("OPENAI_API_KEY"))
        completion = client.chat.completions.create(
            model="gpt-4o-mini-search-preview",
            web_search_options={},
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return completion.choices[0].message.content
