# ScaleSerpBrowserTool

The `ScaleSerpBrowserTool` provides web browsing and search capabilities using the SCALESERP API. This tool allows agents to search the web, browse specific URLs, and extract content from web pages.

## Features

- Web search using SCALESERP API
- Downloading and content extraction from multiple web pages
- HTML to text conversion
- Concurrent page processing for efficiency
- Fallback to ScrapingBee if primary API fails

## Authentication

Requires a SCALESERP API key, which can be set in the environment as `SCALESERP_API_KEY`.

## Methods

### browse_web_tool

```python
async def browse_web_tool(search: str) -> str
```

Browses the web using the SCALESERP API and returns full page contents related to the search term.

**Parameters:**

- `search (str)`: The search query or a "site:" prefixed URL

**Returns:**
Text content from relevant search results.

### download_web_pages

```python
async def download_web_pages(page_urls: list[str] = []) -> str
```

Returns the contents of one or more web pages. Text is extracted from HTML pages.

**Parameters:**

- `page_urls (list[str])`: List of URLs to download

**Returns:**
Combined text content from the pages.

### convert_downloaded_pages

```python
async def convert_downloaded_pages(url_titles: list[tuple], max_count: int) -> list[str]
```

Processes and extracts content from downloaded pages.

**Parameters:**

- `url_titles (list[tuple])`: List of (url, title) tuples
- `max_count (int)`: Maximum content length to return

**Returns:**
List of text content from pages.

### download_pages

```python
async def download_pages(url_titles: list[tuple], max_concurrency=10) -> list[dict]
```

Downloads multiple pages concurrently.

**Parameters:**

- `url_titles (list[tuple])`: List of (url, title) tuples
- `max_concurrency (int)`: Maximum number of concurrent downloads

**Returns:**
List of dictionaries containing downloaded page data.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools.scaleserp_browser import ScaleSerpBrowserTool

# Set up the API key
# os.environ["SCALESERP_API_KEY"] = "your-scaleserp-api-key"

# Create an agent with web browsing capabilities
browser_agent = Agent(
    name="Web Browser",
    instructions="You help users search and browse the web for information.",
    tools=[ScaleSerpBrowserTool()]
)

# Use the agent to search the web
response = browser_agent << "Find information about quantum computing breakthroughs in 2024"
print(response)

# Use the agent to browse specific websites
response = browser_agent << "Visit github.com/supercog-ai/agentic and tell me what it is"
print(response)

# Use the agent to download multiple pages
response = browser_agent << "Download and compare the content from these sites: example.com, example.org, example.net"
print(response)
```

## Search Syntax

The tool supports two main search modes:

1. **Regular search**: `"quantum computing breakthroughs"` 
   - Performs a web search and returns content from the top results

2. **Site-specific search**: `"site:github.com/supercog-ai"`
   - Directly visits the specified URL and returns its content

## HTML Processing

The tool automatically:

- Extracts text from HTML content
- Removes boilerplate elements
- Converts HTML formatting to plain text
- Limits content length to prevent token overflows

## Fallback Mechanism

If SCALESERP fails or times out, the tool automatically:

1. Logs the failure
2. Attempts to use ScrapingBee as an alternative search service
3. Proceeds with the available results from either service
