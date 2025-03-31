# DuckDuckGoSearchTool

The `DuckDuckGoSearchTool` provides a simple interface to search the web using DuckDuckGo. This tool allows agents to perform web searches without requiring API keys or authentication.

## Features

- Free web search without API keys required
- Multiple search types (text, news, images)
- Customizable search parameters
- Region-specific search results
- SafeSearch filtering options

## Initialization

```python
def __init__(region: Optional[str] = "wt-wt", safesearch: str = "moderate", time: Optional[str] = "y", max_results: int = 5, backend: str = "auto", source: str = "text")
```

**Parameters:**

- `region (Optional[str])`: The region for search results (default: "wt-wt")
- `safesearch (str)`: SafeSearch level ("strict", "moderate", or "off") (default: "moderate")
- `time (Optional[str])`: Time range for results ("d" for day, "w" for week, "m" for month, "y" for year) (default: "y")
- `max_results (int)`: Maximum number of results to return (default: 5)
- `backend (str)`: Search backend to use ("auto", "html", or "lite") (default: "auto")
- `source (str)`: Type of search ("text", "news", or "images") (default: "text")

## Methods

### web_search_with_duckduckgo

```python
def web_search_with_duckduckgo(query: str, max_results: int = 10, source: Optional[str] = None) -> List[Dict[str, str]]
```

Perform web search on DuckDuckGo and return metadata.

**Parameters:**

- `query (str)`: The query to search for
- `max_results (int)`: The number of results to return (default: 10)
- `source (Optional[str])`: The source to look from ("text", "news", or "images") (default: None, uses the initialized source)

**Returns:**
A list of dictionaries with search results. The structure varies by source type:

- **Text search**: Each result includes `snippet`, `title`, and `link`
- **News search**: Each result includes `snippet`, `title`, `link`, `date`, and `source`
- **Image search**: Each result includes `title`, `thumbnail`, `image`, `url`, `height`, `width`, and `source`

## Example Usage

```python
from agentic.common import Agent
from agentic.tools import DuckDuckGoSearchTool

# Create a basic search tool with default settings
search_tool = DuckDuckGoSearchTool()

# Create an agent with search capabilities
search_agent = Agent(
    name="Web Researcher",
    instructions="You help users find information on the web.",
    tools=[search_tool]
)

# Use the agent for a basic text search
response = search_agent << "Find information about renewable energy technologies"
print(response)

# Create a tool for news searches
news_search = DuckDuckGoSearchTool(source="news", time="d", max_results=10)

# Create an agent focused on news
news_agent = Agent(
    name="News Researcher",
    instructions="You find and summarize recent news stories.",
    tools=[news_search]
)

# Use the agent for news search
response = news_agent << "What are the latest developments in AI regulation?"
print(response)
```

## Additional Options

### Region Values

The region parameter accepts various region codes, including:

- "wt-wt" (International)
- "us-en" (United States)
- "uk-en" (United Kingdom)
- "ca-en" (Canada)
- "de-de" (Germany)
- "fr-fr" (France)
- "jp-jp" (Japan)

### Backend Options

- "auto": Automatically selects the best backend
- "html": Uses the HTML scraping backend
- "lite": Uses the lighter API backend (may return fewer results)

### Source Types

- "text": Standard web search results
- "news": News article results
- "images": Image search results
