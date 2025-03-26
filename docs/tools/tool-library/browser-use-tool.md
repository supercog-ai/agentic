# BrowserUseTool

The `BrowserUseTool` enables intelligent browser automation through LLM-directed interactions. This tool allows agents to navigate websites, perform complex tasks, and extract information by controlling a browser instance.

## Features

- Full browser automation with LLM control
- Support for authenticated web sessions
- Visual page navigation and interaction
- Content extraction and analysis
- Support for different browser modes (visible or headless)

## Dependencies

- Requires the `playwright` and `browser-use` packages

## Initialization

```python
def __init__(chrome_instance_path: Optional[str] = None, model: str = GPT_4O_MINI)
```

**Parameters:**

- `chrome_instance_path (Optional[str])`: Optional path to Chrome executable (to use the user's browser with cookies and state)
- `model (str)`: LLM model to use for browser automation (default: GPT_4O_MINI)

## Methods

### run_browser_agent

```python
async def run_browser_agent(run_context: RunContext, instructions: str, model: Optional[str] = None) -> list[str|FinishCompletion]
```

Execute a set of instructions via browser automation. Instructions can be in natural language.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `instructions (str)`: Natural language instructions for what to do with the browser
- `model (Optional[str])`: Override the default LLM model

**Returns:**
A list containing the history of browsing actions taken and a FinishCompletion event with token usage information.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools.browser_use import BrowserUseTool

# Create an agent with browser automation capabilities
browser_agent = Agent(
    name="Web Automator",
    instructions="You help users navigate websites and perform tasks online.",
    tools=[BrowserUseTool()]
)

# Use the agent with natural language instructions
response = browser_agent << "Go to weather.gov, search for the weather in Boston, and tell me the forecast for tomorrow."
print(response)

# Using a specific Chrome instance (with user cookies/login state)
chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'  # macOS example
browser_agent = Agent(
    name="Authenticated Browser",
    instructions="You help automate tasks on websites where the user is already logged in.",
    tools=[BrowserUseTool(chrome_instance_path=chrome_path)]
)

response = browser_agent << "Go to my Gmail account and summarize the last 3 unread emails"
print(response)
```

## Browser Paths

Common paths for the `chrome_instance_path` parameter:

- macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Linux: `/usr/bin/google-chrome`

## Typical Use Cases

- Automating web research across multiple sources
- Filling out forms and submitting information
- Extracting structured data from websites
- Performing sequences of actions that require login state
- Testing web applications
