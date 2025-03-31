# Tool Library

Agentic comes with a comprehensive set of built-in tools to help your agents interact with various services and data sources. This library makes it easy to add powerful capabilities to your agents without writing complex code.

## Available Tools

| Tool | Description |
|------|-------------|
| [AirbnbCalendarTool](./airbnb-calendar-tool.md) | Access and analyze Airbnb calendar data from iCal feeds |
| [AuthorizedRestApiTool](./authorized-rest-api-tool.md) | Make authenticated REST API calls with various auth methods |
| [BrowserUseTool](./browser-use-tool.md) | Automate browser interactions with a smart agent |
| [DatabaseTool](./database-tool.md) | Connect to and query SQL databases |
| [DuckDuckGoTool](./duckduckgo-tool.md) | Search the web using DuckDuckGo |
| [FileDownloadTool](./file-download-tool.md) | Download files from URLs |
| [GithubTool](./github-tool.md) | Interact with GitHub repositories and APIs |
| [GoogleNewsTool](./google-news-tool.md) | Access Google News for headlines and articles |
| [HumanInterruptTool](./human-interrupt-tool.md) | Pause execution to request human input |
| [IMAPTool](./imap-tool.md) | Access email inboxes using IMAP protocol |
| [LinkedinDataTool](./linkedin-data-tool.md) | Retrieve data from LinkedIn profiles and companies |
| [MCPTool](./mcp-tool.md) | Universal wrapper for Model Control Protocol (MCP) servers |
| [MeetingBaasTool](./meeting-baas-tool.md) | Manage video meetings, record transcripts, and generate summaries |
| [ImageGeneratorTool](./image-generator-tool.md) | Generate images using OpenAI's image generation API |
| [PlaywrightTool](./playwright-tool.md) | Browser automation using Playwright |
| [RAGTool](./rag-tool.md) | Manage and query knowledge bases using Retrieval Augmented Generation |
| [RestApiTool](./rest-api-tool.md) | Make REST API calls with comprehensive options |
| [ScaleSerpBrowserTool](./scaleserp-browser-tool.md) | Web browsing and search using SCALESERP API |
| [TavilySearchTool](./tavily-search-tool.md) | Web search using Tavily's search engine |
| [TextToSpeechTool](./text-to-speech-tool.md) | Convert text to speech with different voices |
| [WeatherTool](./weather-tool.md) | Get current, forecast, and historical weather information |

## How to Use Tools

Tools can be added to your agent by passing them to the `tools` parameter when creating an agent:

```python
from agentic.common import Agent
from agentic.tools import GoogleNewsTool, WeatherTool

agent = Agent(
    name="News and Weather Agent",
    instructions="You are a helpful assistant that provides news and weather information.",
    tools=[WeatherTool(), GoogleNewsTool()]
)
```

Some tools require API keys or other configuration. These are typically passed during initialization:

```python
from agentic.tools import GithubTool

github_tool = GithubTool(api_key="your_github_token", default_repo="owner/repo")
```

For more information on creating your own tools, see [Tools](../index.md).