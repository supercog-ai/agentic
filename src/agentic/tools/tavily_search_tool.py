from typing import List, Callable
import pandas as pd
import httpx

from agentic.common import RunContext, PauseForInputResult
from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry, Dependency

TAVILY_API_URL = "https://api.tavily.com"

@tool_registry.register(
    name="TavilySearchTool",
    description="Search the web using Tavily",
    dependencies=[],
    config_requirements=[],
)

class TavilySearchTool(BaseAgenticTool):
    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def required_secrets(self) -> dict[str, str]:
        return {"TAVILY_API_KEY": "Tavily API key"}

    def get_tools(self) -> list[Callable]:
        return [
            self.perform_web_search,
            self.query_for_news,
            self.tavily_download_pages,
        ]

    async def query_for_news(
        self, run_context: RunContext, query: str, days_back: int = 1
    ) -> pd.DataFrame | PauseForInputResult:
        """Returns the latest headlines on the given topic."""

        api_key = run_context.get_secret("TAVILY_API_KEY", self.api_key)

        params = {
            "api_key": api_key,
            "query": query,
            "topic": "news",
            "max_results": 10,
            "include_images": False,
            "include_answer": "advanced",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TAVILY_API_URL}/search",
                json=params,
                timeout=90,
            )

        response.raise_for_status()
        results = response.json()

        return pd.DataFrame(results["results"])

    async def perform_web_search(
        self, 
        query: str, 
        include_images: bool = False, 
        include_content: bool = False,
        run_context: RunContext = None
    ) -> List[dict]:
        """Returns a web search result pages and images using the Tavily search engine. Anything
         related to news should use the query_for_news function. Set 'include_content' to return the full page contents.
        Don't use the "site:" filter unless requested explicitly to do so.
        """

        api_key = self.api_key or run_context.get_secret("TAVILY_API_KEY")

        max_results: int = 8
        """Max search results to return, default is 5"""
        search_depth: str = "advanced"
        '''The depth of the search. It can be "basic" or "advanced"'''
        include_domains: List[str] = []
        """A list of domains to specifically include in the search results. Default is None, which includes all domains."""
        exclude_domains: List[str] = []
        """A list of domains to specifically exclude from the search results. Default is None, which doesn't exclude any domains."""
        include_answer: bool = True
        """Include a short answer to original query in the search results. Default is False."""
        include_raw_content: bool = False
        """Include cleaned and parsed HTML of each site search results. Default is False."""

        params = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_domains": include_domains,
            "exclude_domains": exclude_domains,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "include_images": include_images,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TAVILY_API_URL}/search",
                json=params,
                timeout=90,
            )

        response.raise_for_status()
        results = response.json()

        # Concatenate the new rows to the existing DataFrame
        return results['results'] + results.get('images', [])

    async def tavily_download_pages(
        self, run_context: RunContext, urls: list[str], include_images: bool = False
    ) -> pd.DataFrame:
        """Download the content from one or more web page URLS."""
        api_key = run_context.get_secret("TAVILY_API_KEY", self.api_key)

        params = {
            "api_key": api_key,
            "urls": urls,
            "extract_depth": "advanced",
            "include_images": include_images,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TAVILY_API_URL}/extract",
                json=params,
                timeout=90,
            )

        return response.json()

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
