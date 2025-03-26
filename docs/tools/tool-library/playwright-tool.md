# PlaywrightTool

The `PlaywrightTool` provides browser automation capabilities using the Playwright framework. This tool allows agents to navigate websites, extract content, take screenshots, and interact with web elements.

## Features

- Navigate to URLs and retrieve page content
- Extract text content from web pages
- Convert HTML to Markdown for better readability
- Take screenshots of full pages or specific elements
- Click on elements to interact with web pages

## Initialization

```python
def __init__(headless: bool = False)
```

**Parameters:**

- `headless (bool)`: Whether to run browser in headless mode (invisible) or visible mode (default: False)

## Methods

### navigate_to_url

```python
def navigate_to_url(run_context: RunContext, url: str) -> str
```

Navigate to a URL and return the page title.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `url (str)`: URL to navigate to

**Returns:**
The page title, or None if navigation failed.

### extract_text

```python
def extract_text(run_context: RunContext, selector: str, convert_to_markdown: bool = True) -> str
```

Extract text content from elements matching a CSS selector.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `selector (str)`: CSS selector to find elements
- `convert_to_markdown (bool)`: Whether to convert HTML to Markdown (default: True)

**Returns:**
Extracted text or Markdown content.

### take_screenshot

```python
def take_screenshot(run_context: RunContext, selector: str = None, filename: str = None) -> str
```

Take a screenshot of the page or a specific element.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `selector (str)`: Optional CSS selector to screenshot specific element
- `filename (str)`: Optional filename to save screenshot (defaults to timestamp)

**Returns:**
Path to saved screenshot file or error message.

### click_element

```python
def click_element(run_context: RunContext, selector: str) -> str
```

Click an element matching the CSS selector.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `selector (str)`: CSS selector for element to click

**Returns:**
Success or failure message.

### download_pages

```python
def download_pages(run_context: RunContext, pages: List[str]) -> list[tuple[str, str, str]]
```

Downloads the content of multiple pages.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `pages (List[str])`: List of URLs to download

**Returns:**
A list of tuples (url, title, content) for each page.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools.playwright import PlaywrightTool

# Create a browser automation tool with visible browser (for debugging)
browser_tool = PlaywrightTool(headless=False)

# Create an agent with browser automation capabilities
browser_agent = Agent(
    name="Web Browser",
    instructions="You help users navigate and extract information from websites.",
    tools=[browser_tool]
)

# Use the agent to navigate and extract information
response = browser_agent << "Go to https://example.com and extract all paragraph text"
print(response)

# Use the agent to take a screenshot
response = browser_agent << "Go to https://weather.gov and take a screenshot of the forecast"
print(response)

# Use the agent for interactive browsing
response = browser_agent << "Go to https://news.ycombinator.com and click on the top story"
print(response)
```

## CSS Selectors

The tool uses CSS selectors to identify elements. Some common examples:

- `p` - All paragraph elements
- `#main` - Element with ID "main"
- `.article` - Elements with class "article"
- `h1, h2, h3` - All heading elements
- `article > p` - Paragraphs directly inside article elements

## Browser Management

The tool manages browser resources automatically:

- Browser is launched on first use
- Resources are cleaned up properly when the agent is done
- If the browser crashes, it will be restarted on next use
