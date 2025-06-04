# TavilySearchTool

The `TavilySearchTool` provides web search capabilities using [Tavily's search engine API](https://docs.tavily.com/welcome). This tool allows your agents to search the web, get news headlines, and download page content.

## Features

- Perform general web searches
- Query specifically for news content
- Download and extract content from web pages

## Authentication

Requires a Tavily API key, which can be:
- Passed during initialization
- Set in environment variables
- Stored in Agentic's secrets system as `TAVILY_API_KEY`

## Methods

### perform_web_search

```python
async def perform_web_search(query: str, include_images: bool, include_content: bool, thread_context: RunContext) -> List[dict]
```

Performs a web search using Tavily's search engine and returns results with metadata.

**Parameters:**

- `query (str)`: The search query
- `include_images (bool)`: Whether to include images in the results
- `include_content (bool)`: Whether to return the full page contents
- `thread_context (RunContext)`: The agent's running context

**Returns:**
A list of dictionaries containing search results with metadata such as titles, URLs, and snippets.

### query_for_news

```python
async def query_for_news(thread_context: RunContext, query: str, days_back: int = 1) -> pd.DataFrame | PauseForInputResult
```

Returns the latest headlines on a given topic using Tavily's news search.

**Parameters:**

- `thread_context (RunContext)`: The agent's running context
- `query (str)`: The news topic to search for
- `days_back (int)`: Number of days back to search (default: 1)

**Returns:**
A pandas DataFrame containing news articles related to the query.

### tavily_download_pages

```python
async def tavily_download_pages(thread_context: RunContext, urls: list[str], include_images: bool = False) -> pd.DataFrame
```

Downloads content from one or more web page URLs using Tavily's content extraction API.

**Parameters:**

- `thread_context (RunContext)`: The agent's running context
- `urls (list[str])`: List of URLs to download
- `include_images (bool)`: Whether to include images in the results

**Returns:**
A pandas DataFrame or JSON response containing the extracted content.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools import TavilySearchTool

# Create an agent with web search capabilities
search_agent = Agent(
    name="Web Researcher",
    instructions="You are a helpful assistant that searches the web for information.",
    tools=[TavilySearchTool(api_key="your_tavily_api_key")]
)

# Use the agent
response = search_agent << "Find me the latest news on artificial intelligence breakthroughs"
print(response)
```

## Helper Methods

The tool also includes helper methods for processing search results and formatting sources:

- `_deduplicate_and_format_sources`: Formats search results into a readable string with deduplication
- Various HTTP request handling methods

## Notes

- The tool automatically handles authentication with the Tavily API
- JSON responses are automatically converted to pandas DataFrames for easier processing
- For more information about Tavily's search API, visit [tavily.com](https://tavily.com)
