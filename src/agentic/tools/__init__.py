# Minimalist initialization with lazy loading
__path__ = __import__('pkgutil').extend_path(__path__, __name__)

# Mapping of tool names to their source modules
_TOOL_MAPPING = {
    "AirbnbCalendarTool": "airbnb_calendar_tool",
    "AuthorizedRestApiTool": "auth_rest_api_tool",
    "AutomaticTools": "automatic_tools",
    "BaseAgenticTool": "base",
    "BrowserUseTool": "browser_use",
    "DatabaseTool": "database_tool",
    "DuckDuckGoTool": "duckduckgo",
    "ExampleTool": "example_tool",
    "FileDownloadTool": "file_download",
    "GithubTool": "github_tool",
    "GoogleNewsTool": "google_news",
    "HumanInterruptTool": "human_interrupt",
    "ImageGeneratorTool": "image_generator",
    "IMAPTool": "imap_tool",
    "LinkedinDataTool": "linkedin_tool",
    "MCPTool": "mcp_tool",
    "MeetingBaasTool": "meeting_tool",
    "OAuthTool": "oauth_tool",
    "PlaywrightTool": "playwright",
    "PodcastTool": "podcast_tool",
    "RAGTool": "rag_tool",
    "RestApiTool": "rest_api_tool",
    "ScaleSerpBrowserTool": "scaleserp_browser",
    "TavilySearchTool": "tavily_search_tool",
    "TextToSpeechTool": "text_to_speech_tool",
    "UnitTestingTool": "unit_test_tool",
    "WeatherTool": "weather_tool",
}

__all__ = [
    "AirbnbCalendarTool",
    "AuthorizedRestApiTool",
    "AutomaticTools",
    "BaseAgenticTool",
    "BrowserUseTool",
    "DatabaseTool",
    "DuckDuckGoTool",
    "ExampleTool",
    "FileDownloadTool",
    "GithubTool",
    "GoogleNewsTool",
    "HumanInterruptTool",
    "ImageGeneratorTool",
    "IMAPTool",
    "LinkedinDataTool",
    "MCPTool",
    "MeetingBaasTool",
    "OAuthTool",
    "PlaywrightTool",
    "PodcastTool",
    "RAGTool",
    "RestApiTool",
    "ScaleSerpBrowserTool",
    "TavilySearchTool",
    "TextToSpeechTool",
    "UnitTestingTool",
    "WeatherTool",
]

# Tool cache to avoid repeated imports
_tool_cache = {}

def __getattr__(name):
    """
    Lazily import tools only when they're actually requested.
    This prevents circular imports during module initialization.
    """
    if name in _TOOL_MAPPING:
        module_name = _TOOL_MAPPING[name]
        
        # Check cache first
        if name in _tool_cache:
            return _tool_cache[name]
            
        # Import the module and get the tool class
        try:
            module = __import__(f"agentic.tools.{module_name}", fromlist=[name])
            tool = getattr(module, name)
            
            # Cache for future use
            _tool_cache[name] = tool
            return tool
        except (ImportError, AttributeError) as e:
            raise AttributeError(f"Failed to import {name} from module {module_name}: {e}")
    
    # Handle the case where __getattr__ is called for something not in our mapping
    raise AttributeError(f"module 'agentic.tools' has no attribute '{name}'")

# Support for dir() to show available tools
def __dir__():
    """Return list of available attributes/tools."""
    return sorted(__all__)
