from typing import Callable

from openai import OpenAI

from agentic.common import Agent, AgentRunner, RunContext
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
            self.launch_model
        ]

    def launch_model(self,  run_context: RunContext):
        """Function to launch the openAI model. Use this function before calling perform_web_search()."""
        self.client = OpenAI(api_key=run_context.get_secret("OPENAI_API_KEY"))

    def perform_web_search(self, prompt: str):
        """
        Function to prompt the model to perform a web search.

        Args:
            prompt: The message to prompt the model with

        Returns:
            The message returned by the model
        """
        completion = self.client.chat.completions.create(
            model="gpt-4o-search-preview",
            web_search_options={},
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return completion.choices[0].message.content
    
    def _deduplicate_and_format_sources(
            self, 
            sources_list, 
            max_tokens_per_source, 
            include_raw_content=True,
            missing_pages_list: list = [],
        ) -> str:
        """
        Takes a list of search responses and formats them into a readable string.
        Limits the raw_content to approximately max_tokens_per_source. If raw_content is not returned
        from Tavily then the page is added to the missing_pages_list.
    
        Args:
            search_responses: List of search response dicts, each containing:
                - query: str
                - results: List of dicts with fields:
                    - title: str
                    - url: str
                    - content: str
                    - score: float
                    - raw_content: str|None
            max_tokens_per_source: int
            include_raw_content: bool
                
        Returns:
            str: Formatted string with deduplicated sources
        """
        # Deduplicate by URL
        unique_sources = {source['url']: source for source in sources_list}

        # Format output
        formatted_text = "Sources:\n\n"
        for i, source in enumerate(unique_sources.values(), 1):
            formatted_text += f"Source {source['title']}:\n===\n"
            formatted_text += f"URL: {source['url']}\n===\n"
            formatted_text += f"Most relevant content from source: {source['content']}\n===\n"
            if include_raw_content:
                # Using rough estimate of 4 characters per token
                char_limit = max_tokens_per_source * 4
                # Handle None raw_content
                raw_content = source.get('raw_content', '')
                if raw_content is None:
                    raw_content = ''
                    missing_pages_list.append(source['url'])
                if len(raw_content) > char_limit:
                    raw_content = raw_content[:char_limit] + "... [truncated]"
                formatted_text += f"Full source content limited to {max_tokens_per_source} tokens: {raw_content}\n\n"
                    
        return formatted_text.strip()

if __name__ == "__main__":
    
    from agentic.models import GPT_4O_MINI
    MODEL=GPT_4O_MINI 

    agent = Agent(
        name="Web Searching Agent",
        welcome="I am a simple agent here to help answer your weather questions.",
        instructions="You are a helpful assistant that can search the web for information.",
        model=MODEL,
        tools=[OpenAIWebSearchTool()],
    )

    agent = AgentRunner(agent)
    print(agent.turn("What's the weather like today in London, Ontario?"))
