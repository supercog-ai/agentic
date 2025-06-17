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
    
    def format_sources(self, content: str):
        """
        Replaces all embedded Markdown links with index numbers and returns a tuple:
        (formatted_content, sources_dict)
        where the sources_dict maps index numbers to URLs, and formatted_content is the string result 
        without long links.
        """
        # Pattern to match Markdown links: [text](url)
        pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')
        sources = {}
        idx = 1

        def replacer(match):
            nonlocal idx
            text = match.group(1)
            url = match.group(2)

            # Don't add existing URLs in the sources dict
            for key, value in sources.items():
                if value == url:
                    return key
            
            # If it's not already a source, add it
            sources[str(idx)] = url
            replacement = f"{idx}"
            idx += 1
            return replacement

        formatted_content = pattern.sub(replacer, content)
        print(str(formatted_content) + "\n\n" + str(sources))
        return formatted_content, sources
