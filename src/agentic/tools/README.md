# Tools Documentation


# Airbnb Calendar Tool
The Airbnb Calendar Tool is a Python-based utility designed to access, analyze, and manage Airbnb calendar data from iCal feeds. It provides functionality to retrieve booking information, check availability, gather booking statistics, and identify blocked dates for Airbnb listings.

## Key Features
- Fetch and parse Airbnb calendar data from iCal feeds
- List events/bookings within a specified date range
- Check property availability for given dates
- Generate booking statistics including occupancy rates
- Identify blocked or unavailable dates

## Main Functions

### Calendar Data Retrieval and Parsing
**_fetch_calendar**
- Fetches calendar data from a given URL
- Handles webcal:// to https:// conversion if needed

**_parse_calendar**
- Parses raw iCal data into a list of event dictionaries
- Categorizes events as "block" or "reservation"

### Event Management
**list_events**
- Lists all events/bookings within a specified date range
- Filters events based on optional start and end dates

**check_availability**
- Checks if the property is available for a specific date range
- Identifies and reports any conflicts with existing bookings

### Statistics and Analysis
**get_booking_stats**
- Calculates booking statistics for a specified date range
- Provides total days, booked days, booking count, and occupancy rate

**get_blocked_dates**
- Retrieves a list of blocked or unavailable dates
- Can be filtered by an optional date range

## Usage Notes
- Requires an Airbnb calendar URL (iCal format) to be set as the AIRBNB_CALENDAR_URL secret
- All date inputs should be in ISO format (YYYY-MM-DD)
- The tool handles various error scenarios and returns JSON-formatted responses
- Depends on the 'icalendar' library (version 5.0.11)
- Implements error handling and input validation for robust operation
- Designed to work within an asynchronous context (all main functions are async)

---


# Auth Rest Api Tool
The Auth Rest Api Tool is an extension of the RestApiTool that provides authenticated access to REST API endpoints. It supports various authentication methods including bearer tokens, basic auth, parameter-based auth, and custom header auth.

## Key Features
- Supports multiple authentication types (bearer, basic, parameter, header)
- Automatic handling of authentication for REST API requests
- Provides methods for common HTTP operations (GET, POST, PUT, PATCH, DELETE)
- Customizable token configuration

## Main Functions

### Authentication Setup

**get_auth_variable**
- Prepares the authentication configuration based on the specified token type
- Retrieves the necessary credentials from the run context secrets

### HTTP Operations

**get_resource**
- Performs a GET request to the specified URL with authentication

**post_resource**
- Performs a POST request to the specified URL with authentication
- Supports JSON and form data content types

**put_resource**
- Performs a PUT request to the specified URL with authentication

**patch_resource**
- Performs a PATCH request to the specified URL with authentication

**delete_resource**
- Performs a DELETE request to the specified URL with authentication

### Additional Utilities
**add_request_header**
- Adds a custom header to the request (inherited from parent class)

**debug_request**
- Provides debugging information for requests (inherited from parent class)

## Usage Notes
- The tool requires proper configuration of token type, token variable, and token name during initialization
- Authentication credentials must be stored in the run context secrets
- For basic authentication, the token should be formatted as "<user>:<password>"
- The tool automatically handles authentication for each request based on the configured token type
- Error handling is implemented for missing token variables in secrets
- The tool is designed to work asynchronously, with all main functions being coroutines


---

# Automatic Tools
Automatic Tools is a Python-based tool that provides a flexible framework for managing and utilizing various tools within an AI agent environment. It allows for dynamic tool discovery, enabling, and file handling capabilities.

## Key Features
- Dynamic tool management (classes and functions)
- Tool search functionality based on purpose
- Ability to enable tools for an AI agent
- Universal file reading capability (including URLs)

## Main Functions

**Tool Management**

- `get_tool_listing(show_connections_only: Optional[bool] = False) -> list[dict]`
  - Returns a list of all available tools with their names and descriptions.

- `search_for_tool(purpose: str) -> list[str]`
  - Searches for one or more tools related to the indicated purpose, using LLM-based matching or keyword search as a fallback.

- `enable_agent_tool(tool_name: str, run_context: RunContext) -> str`
  - Enables the AI agent to use the tool with the indicated name, adding it to the agent's tool set.

**File Handling**

- `universal_read_file(file_name: str) -> Any`
  - Reads the contents of any file type, including support for reading from URLs.

## Usage Notes
- The tool is designed to work within an AI agent environment, utilizing a `RunContext` for certain operations.
- It supports both tool classes and tool functions, which should be provided during initialization.
- The tool uses LLM (Language Model) capabilities for advanced tool searching.
- File reading supports various formats, including text and pandas DataFrames.
- Error handling is implemented for file reading and tool enabling processes.
- The tool relies on external components like `RAGTool` and `FileDownloadTool` for some functionalities.

---


# Base
Base is an abstract base class for creating Agentic tools in Python. It provides a foundation for implementing tool classes with a consistent interface and serialization support.

## Key Features
- Abstract base class for Agentic tools
- Defines a common interface for tool implementation
- Supports custom serialization for Ray

## Main Functions

**Initialization**

`__init__`
- Abstract method for initializing the tool (to be implemented by subclasses)

**Tool Retrieval**

`get_tools`
- Abstract method that should return a list of callable tools (to be implemented by subclasses)

**Serialization**

`__getstate__`
- Custom serialization method for Ray compatibility

## Usage Notes
- This class is not meant to be instantiated directly but should be subclassed
- Subclasses must implement the `__init__` and `get_tools` methods
- The `get_tools` method should return a list of callable functions representing the tool's capabilities
- When using with Ray, only non-private attributes (those not starting with '_') will be serialized
- Proper type hinting is used to enhance code readability and IDE support


---


# Browser Use

Browser Use is a tool that automates browser interactions using a smart agent. It allows execution of natural language instructions for web browsing tasks and returns the history of actions taken.

## Key Features
- Automates browser interactions with AI-driven agents
- Supports multiple language models (GPT, Gemini, Claude, etc.)
- Can use the user's existing Chrome browser instance (optional)
- Tracks and reports token usage for language model interactions

## Main Functions

**Browser Automation**

`run_browser_agent`
- Executes a set of instructions via browser automation
- Accepts natural language instructions
- Returns the history of browsing actions taken

## Usage Notes
- Requires installation of 'playwright' (version 1.50.0) and 'browser-use' (version 0.1.37) packages
- API keys for the chosen language model must be properly set in the environment
- Chrome instance path can be specified for using the user's existing browser (optional, use with caution)
- Supports various language models, including GPT, Gemini, Claude, and others
- Token usage is tracked and reported for each run

## Implementation Details

**Model Initialization**

`_initialize_llm`
- Initializes the language model based on the specified model string
- Supports Gemini models directly, uses Litellm for other model types

**API Key Retrieval**

`_get_api_key`
- Retrieves the appropriate API key based on the specified model
- Supports keys for OpenAI, Anthropic, Google (Gemini), and attempts to infer keys for other providers

**Token Usage Tracking**

`TokenCounterStdOutCallback`
- Tracks and reports token usage for input and output
- Provides total token counts for the entire session

Note: The tool is designed to work with various language models, but proper API keys and environment setup are required for each model type. The code includes a TODO comment to implement "required_secrets" for API key validation.

---


# Database Tool
The Database Tool is a Python-based utility for interacting with SQL databases. It provides a set of functions to connect to various types of databases, execute SQL queries, and retrieve database information. The tool is designed to work with different database systems including PostgreSQL, MySQL, and Microsoft SQL Server.

## Key Features
- Connect to various SQL databases using connection strings or CLI commands
- Execute SQL queries and retrieve results as pandas DataFrames or dictionaries
- Determine the type and SQL dialect of the connected database
- Handle different connection string formats and parse them appropriately
- Manage database connections and handle connection errors

## Main Functions

### Query Execution
**run_database_query**
- Executes a SQL query against the connected database
- Returns results as a pandas DataFrame or a dictionary
- Handles various types of errors and provides status messages

### Database Information
**get_database_type**
- Returns the type and SQL dialect of the connected database (e.g., PostgreSQL, MySQL, MSSQL)

## Usage Notes
- The tool requires a valid database connection string or CLI command to connect to a database
- Supported database types include PostgreSQL, MySQL, and Microsoft SQL Server
- Connection strings can be provided in SQLAlchemy format or as CLI commands
- The tool uses SQLAlchemy as the underlying engine for database operations
- Error handling is implemented for various scenarios, including connection errors and query execution failures
- The tool can pause for input if a connection string is missing or invalid
- Database credentials should be handled securely and not hardcoded in the connection string

The tool also includes internal methods for parsing connection strings, creating database engines, and checking for missing connections, but these are not directly exposed as main functions for external use.

---


# Duckduckgo
Duckduckgo is a wrapper for the DuckDuckGo Search API, providing a free and easy-to-use interface for web searching without requiring any setup. It allows users to perform text, news, and image searches using DuckDuckGo's search engine.

## Key Features
- Perform web searches using DuckDuckGo's search engine
- Support for text, news, and image search types
- Customizable search parameters including region, safesearch, and time range
- No authentication or API key required

## Main Functions

**Web Search**
**web_search_with_duckduckgo**
- Performs a web search on DuckDuckGo and returns metadata for the results
- Parameters:
  - query: The search query string
  - max_results: The maximum number of results to return (default: 10)
  - source: The type of search to perform (text, news, or images)
- Returns a list of dictionaries containing metadata about the search results

## Usage Notes
- Requires the 'duckduckgo-search' Python package (version 7.4.2) to be installed
- The tool is registered under the name "DuckDuckGoTool" in the tool registry
- Default search parameters can be customized by setting class attributes:
  - region: Search region (default: "wt-wt")
  - safesearch: SafeSearch setting (options: strict, moderate, off; default: "moderate")
  - time: Time range for results (options: d, w, m, y; default: "y")
  - max_results: Maximum number of results to return (default: 5)
  - backend: Search backend to use (options: auto, html, lite; default: "auto")
  - source: Type of search to perform (options: text, news, images; default: "text")
- The tool uses the 'duckduckgo-search' package, which may have limitations on the number of results returned


---


# Example Tool
Example Tool is a Python-based utility designed to perform various operations, including handling tabular data and managing API authentication. It provides a set of functions that can be used in an agent-based system, allowing for flexible and extensible tool usage.

## Key Features
- Provides multiple tool functions for different operations
- Supports both synchronous and asynchronous function execution
- Handles API authentication and secret management
- Returns tabular data as pandas DataFrames
- Allows for pausing execution to request user input for missing information

## Main Functions

### Data Operations
**tool_returns_tabluar_data**
- Asynchronously processes a query and returns the result as a pandas DataFrame

### Authentication and Configuration
**sometimes_auth_required**
- Handles API authentication, requesting an API key if not provided
- Demonstrates the use of run context for secret management

### Miscellaneous
**tool_function_one**
- A placeholder function that takes two string parameters and returns a string

## Usage Notes
- The tool requires the following package installations:
  ```
  pip install pydantic
  pip install requests
  ```
- An API key can be provided during initialization or requested during execution
- The tool integrates with a RunContext object for metadata and secret management
- Functions that return records are encouraged to use pandas DataFrames
- The tool supports pausing execution to request additional information from the user
- All tool functions must include the special 'run_context' parameter

---


# File Download
This tool provides functionality for downloading files and content from URLs. It offers methods to save files locally or retrieve their contents directly.

## Key Features
- Download files from URLs and save them locally
- Retrieve file contents directly from URLs
- Handle HTML content by converting it to plain text
- Asynchronous file downloading for improved performance

## Main Functions

### File Download
**download_url_as_file**
- Downloads a file from a given URL and saves it locally
- Returns the name of the saved file

**download_file_content**
- Downloads content from a given URL and returns it as a string
- Handles HTML content by converting it to plain text
- Limits the returned content to a specified number of characters

## Usage Notes
- The tool uses asynchronous operations for file downloading, which can improve performance for multiple downloads
- HTML content is automatically converted to plain text when using `download_file_content`
- File names are generated based on the URL if not provided
- The tool handles redirects when downloading files
- Error messages are returned as strings if downloads fail
- Content retrieval is limited to 4000 characters by default when using `download_file_content`
- The tool requires the following Python packages: httpx, aiofiles, html2text, and requests


---

# Generate Tool Doc
Generate Tool Doc is a Python tool designed to automatically create comprehensive documentation for Python tools. It analyzes Python files in a specified directory, extracts relevant information, and uses the Claude API to generate structured documentation for each tool.

## Key Features
- Recursively scans a directory for Python files, excluding utils folders and __init__.py files
- Generates documentation prompts based on the content of each Python file
- Utilizes the Claude API to create detailed, structured documentation for each tool
- Sorts generated documentation alphabetically by tool name
- Compiles all documentation into a single README.md file

## Main Functions

**File Processing**
get_python_files(directory: str) -> List[str]:
- Retrieves all Python files in the specified directory, excluding utils folders and __init__.py files

read_file_content(file_path: str) -> str:
- Reads the content of a given file

get_tool_name(file_path: str) -> str:
- Extracts the tool name from the file path

**Documentation Generation**
generate_doc_prompt(code: str, tool_name: str) -> str:
- Creates a prompt for the Claude API to generate documentation based on the tool's code and name

call_claude_api(prompt: str, api_key: str) -> str:
- Sends a request to the Claude API to generate documentation based on the provided prompt

**Output Handling**
sort_documentation_alphabetically(docs: List[Dict[str, str]]) -> List[Dict[str, str]]:
- Sorts the generated documentation entries alphabetically by tool name

save_to_readme(docs: List[Dict[str, str]], output_file: str = "README.md") -> None:
- Saves the generated documentation to a README.md file

**Main Function**
generate_documentation(tools_dir: str, api_key: str, output_file: str = "README.md") -> None:
- Orchestrates the entire documentation generation process

## Usage Notes
- Requires Python 3.6 or higher
- Depends on the following libraries: os, re, glob, json, requests, typing, sys, argparse
- An Anthropic API key is required to use the Claude API for documentation generation
- The tool is designed to be run from the command line with arguments for the directory to scan, output file path, and API key
- Generated documentation follows a specific structure, including sections for general description, key features, main functions, and usage notes
- The tool focuses on documenting the main functions declared in the get_tools method of each Python file
- Only features and functions that are actually implemented in the code are included in the documentation

---


# Github Tool
The Github Tool is a Python-based utility for interacting with GitHub's API. It provides a range of functionalities for managing repositories, issues, pull requests, and performing various GitHub-related operations.

## Key Features
- OAuth authentication for GitHub API access
- Repository management (search, create, delete)
- Issue and pull request handling
- User information retrieval
- Code search within repositories
- File download from repositories

## Main Functions

### Repository Management
**search_repositories**
- Search for GitHub repositories based on keywords, language, and sorting criteria

**create_repository**
- Create a new GitHub repository

**delete_repository**
- Delete an existing GitHub repository

**get_repository_contents**
- Retrieve the contents of a specified repository

**list_user_repositories**
- List repositories for the authenticated user

### Issue Management
**create_github_issue**
- Create a new issue in a GitHub repository

**get_github_issues**
- Retrieve a list of issues for a repository

**get_github_issue_comments**
- Get comments for a specific GitHub issue

**add_comment_to_issue**
- Add a comment to an existing GitHub issue

### Pull Request Management
**create_pull_request**
- Create a new pull request

**get_pull_requests**
- Retrieve a list of pull requests for a repository

**get_pr_reviews**
- Get reviews for a specific pull request

**get_pr_comments**
- Retrieve comments on a specific pull request

**list_repository_pull_requests**
- List pull requests for a specific repository

### User Information
**get_user_info**
- Retrieve information about a GitHub user

### Code Search and File Operations
**search_in_repo**
- Search for code within a specific repository

**download_repo_file**
- Download a file from a GitHub repository

## Usage Notes
- The tool requires GitHub API credentials (API key or OAuth token) for authentication
- A default repository can be configured for operations that require a repository
- The tool uses asynchronous HTTP requests for improved performance
- Some functions return pandas DataFrames for easy data manipulation and viewing
- Error handling is implemented for most API interactions
- The tool supports both personal access tokens and OAuth authentication flow

This documentation reflects the actual implemented functionality in the provided code for the Github Tool.

---


# Google News

Google News is a tool for accessing and analyzing news articles from Google News. It provides various functions to retrieve, search, and analyze news content across different categories, locations, and topics.

## Key Features
- Retrieve top headlines from Google News
- Search for news articles based on specific topics or queries
- Get news from specific categories or locations
- Analyze local and trending topics
- Utilize advanced search syntax for precise news queries
- Download and extract content from news articles

## Main Functions

### News Retrieval
**get_top_headlines**
- Retrieves top headlines for a specified language and country

**query_topic**
- Retrieves news articles related to a specific topic

**query_news**
- Searches for news articles based on a given query and various parameters, including date range, exact phrases, excluded terms, and more

**get_category_news**
- Retrieves news from a specific category (e.g., WORLD, NATION, BUSINESS)

**get_location_news**
- Retrieves news articles related to a specific location

### Topic Analysis
**get_local_topics**
- Analyzes news to extract trending topics for a specific location

**get_trending_topics**
- Retrieves a list of currently trending topics on Google News

### Search Assistance
**explain_search_syntax**
- Provides an explanation of the advanced search syntax for Google News RSS

### Article Processing
**download_news_article**
- Downloads and extracts the content of a news article, resolving internal Google News links if necessary

## Usage Notes
- The tool requires the `ScaleSerpBrowserTool` for certain operations
- Some functions return results as pandas DataFrames for easy data manipulation
- The tool uses the `GoogleNewsFeed` class for interacting with Google News
- Advanced search options are available for precise querying of news articles
- The trending topics feature is an approximation based on word frequency in headlines
- The tool can handle internal Google News links and resolve them to actual article URLs
- Error handling is implemented for article downloads, with error messages returned in case of failures

---


# Image Generator
This tool provides functionality for generating images using OpenAI's GPT-4V model through the OpenAI API. It's designed to create images based on text prompts and return a publicly accessible URL for the generated image.

## Key Features
- Image generation based on text prompts
- Integration with OpenAI's API for image creation
- Secure API key management through run context

## Main Functions

### Image Generation
**generate_image**
- Generates an image based on a given text prompt
- Uses OpenAI's API for image creation
- Returns a markdown-formatted string with the image URL

## Usage Notes
- Requires an OpenAI API key to function
- The API key can be provided through the run context or set directly on the tool instance
- If no API key is available, the tool will pause and request input for the API key
- The tool returns the generated image as a markdown-formatted URL string
- Error handling is implemented to catch and report any issues during image generation
- This tool extends the BaseAgenticTool class and is designed to work within a larger framework

---


# Imap Tool
The Imap Tool is a Python-based utility for accessing and managing email inboxes using the IMAP protocol. It provides functionality to retrieve, list, send, and save draft emails, with a focus on Gmail integration.

## Key Features
- Connect to Gmail accounts using IMAP
- Retrieve emails with various filtering options
- List emails and email folders
- Send emails and save email drafts
- Process email attachments
- Search emails using IMAP search criteria
- Track read/unread status of emails

## Main Functions

### Email Retrieval and Listing
**retrieve_emails**
- Retrieves emails from a specified folder without tracking read status
- Supports filtering by date, recipient, subject, and custom search criteria

**retrieve_emails_once**
- Retrieves emails from a specified folder while tracking which emails have been read
- Only returns emails that haven't been processed before

**list_emails**
- Lists emails in the inbox with optional filtering
- Supports limiting the number of results and filtering by subject words

**list_folders**
- Lists all available folders in the email account

### Email Composition and Sending
**send_email**
- Sends an email message
- Can optionally save as a draft instead of sending

**save_email_draft**
- Saves an email message as a draft

### Utility Functions
**validate_imap_search_criteria**
- Validates and optionally fixes IMAP search criteria

**process_email**
- Processes an email message, extracting subject, sender, date, body, and attachments

**decode_email_header**
- Decodes email subject or sender information

**get_text_from_html**
- Converts HTML content to plain text

## Usage Notes
- Requires Gmail account credentials (email address and app password)
- Uses IMAP for email retrieval and SMTP for sending emails
- Supports various Gmail folders (Inbox, Sent Mail, Drafts, etc.)
- Implements email read tracking using a database (SQLModel)
- Handles email attachments, saving them to a specified directory
- Provides detailed logging and error handling
- Requires the following dependencies:
  - beautifulsoup4 (version 4.13.3)
  - sqlmodel (version 0.0.22)
- Users need to create an App Password for their Gmail account to use this tool
- The tool includes methods for testing credential validity

---


# LinkedIn Tool
The LinkedIn Tool is a Python-based utility for retrieving and searching LinkedIn data using the RapidAPI LinkedIn Data API. It provides functionalities to fetch profile information, company details, and perform people searches on LinkedIn.

## Key Features
- Retrieve LinkedIn profile information by URL
- Get company information by username or domain
- Search for LinkedIn profiles based on various criteria
- Asynchronous API requests for improved performance
- Integration with RapidAPI for LinkedIn data access

## Main Functions

### Profile Information
**get_linkedin_profile_info**
- Retrieves detailed profile information given a LinkedIn profile URL

### Company Information
**get_company_linkedin_info**
- Fetches company information using either a company username or domain

### People Search
**linkedin_people_search**
- Searches for LinkedIn profiles based on name, location, job title, and company

## Usage Notes
- Requires a RapidAPI key set as an environment variable (RAPIDAPI_KEY)
- Utilizes asynchronous HTTP requests for efficient API interactions
- Returns data in pandas DataFrame format for easy manipulation and analysis
- Handles various error scenarios and provides informative error messages
- Includes a location search function to convert location names to LinkedIn geo IDs

## Additional Functions

### API Key and Headers
**get_api_key**
- Retrieves the RapidAPI key from environment variables

**get_headers**
- Generates the required headers for API requests

### Location Search
**search_location**
- Searches for LinkedIn location ID by keyword

### Test Function
**linkedin_people_search_tst**
- A test function that returns mock search results (not connected to the API)

## Error Handling
- Checks for the presence of an API key before making requests
- Handles HTTP errors and provides descriptive error messages
- Manages cases where no data is found or the API request fails

## Dependencies
- httpx: For asynchronous HTTP requests
- pandas: For data manipulation and DataFrame creation
- os: For environment variable access
- typing: For type hinting


---


# Mcp Tool
Mcp Tool is a universal wrapper for MCP (Model Control Protocol) tools that can work with any MCP server. It provides a flexible interface to initialize, manage, and interact with MCP tools through a Python-based client.

## Key Features
- Dynamic loading of MCP tools from a server
- Conversion of MCP tools to callable Python functions
- Asynchronous communication with MCP server
- Support for custom tool selection
- Automatic session management and cleanup

## Main Functions

### Initialization and Setup
**MCPTool.__init__**
- Initializes the MCP tool wrapper with server parameters and optional tool selection

**MCPTool._init_session**
- Asynchronously initializes the MCP session and loads available tools

### Tool Management
**MCPTool.get_tools**
- Retrieves available MCP tools and converts them to callable Python functions
- Generates documentation for each tool's parameters

### Tool Execution
**MCPTool.call_tool**
- Asynchronously calls an MCP tool with given arguments in OpenAI format

### Cleanup
**MCPTool.cleanup**
- Performs cleanup of MCP session and connections

**MCPTool.__del__**
- Ensures cleanup is performed when the object is deleted

## Usage Notes
- The tool requires an MCP server to be available and specified during initialization
- Tool functions are dynamically generated based on the tools provided by the MCP server
- Each tool function includes auto-generated documentation describing its parameters
- The tool supports both synchronous and asynchronous usage patterns
- Error handling for missing required parameters is implemented in the tool wrapper functions
- The tool automatically manages the lifecycle of the MCP session, including cleanup
- Custom environment variables can be passed to the MCP server during initialization
- The tool supports filtering for a specific tool by name if provided during initialization

---


# Meeting Tool
The Meeting Tool is a comprehensive solution for managing video meetings, including joining calls, recording transcripts, generating summaries, and storing meeting information. It integrates with external services like MeetingBaaS and OpenAI to provide advanced functionality.

## Key Features
- Join video meetings with a bot
- Record meeting transcripts
- Generate meeting summaries using AI
- List and retrieve information about recorded meetings
- Process webhooks for real-time meeting updates
- Check bot status during meetings
- Store meeting data in a local database
- Index meeting summaries for efficient searching

## Main Functions

### Meeting Management
**join_meeting**
- Dispatches a bot to join a specified meeting

**check_bot_status**
- Retrieves the current status of a bot in a meeting

### Meeting Data Retrieval
**get_meeting_transcript**
- Fetches and stores the transcript for a specific meeting

**get_meeting_summary**
- Generates or retrieves a summary for a specific meeting

**list_meetings**
- Provides a list of all recorded meetings

**get_meeting_info**
- Retrieves detailed information about a specific meeting or searches meeting data based on a user query

### Webhook Processing
**process_webhook**
- Handles incoming webhook data from MeetingBaaS, updating meeting status and processing completed meetings

## Usage Notes
- Requires MeetingBaaS API key and OpenAI API key to be set in the configuration
- Uses SQLite database to store meeting information locally
- Integrates with Weaviate for vector search capabilities on meeting summaries
- Webhook processing requires a publicly accessible URL (uses DEVTUNNEL_HOST environment variable)
- The tool initializes database and vector search components lazily to optimize resource usage
- Supports serialization for distributed computing environments (e.g., Ray)
- Error handling is implemented for most operations, with detailed error messages returned

This tool provides a robust set of features for managing and analyzing video meetings, with a focus on AI-powered summarization and efficient data retrieval. It's designed to work in conjunction with external services and local data storage for a comprehensive meeting management solution.

---


# OAuth Tool
OAuth Tool is a base class for implementing OAuth authentication flows in Python. It provides a framework for managing OAuth configurations, initiating authentication processes, and handling token exchanges.

## Key Features
- Configurable OAuth flow with customizable parameters
- Environment variable and secrets management for secure credential storage
- Automatic token retrieval and storage
- Extensible design for specific OAuth implementations

## Main Functions

**authenticate**
- Initiates or continues the OAuth authentication flow
- Checks for existing tokens or authorization codes
- Returns authentication status or initiates a new OAuth flow

## Usage Notes
- Requires proper configuration of OAuth parameters (authorize URL, token URL, client ID, client secret, scopes)
- Depends on environment variables or a secrets database for storing sensitive information
- Utilizes asyncio for asynchronous operations
- Designed to be subclassed for specific OAuth provider implementations
- Requires a RunContext object for managing OAuth state and callbacks

## Implementation Details

### Configuration
**OAuthConfig**
- Dataclass for storing OAuth configuration parameters
- Includes authorize_url, token_url, client_id_key, client_secret_key, scopes, and tool_name

### Core Methods
**get_tools**
- Returns a list of callable tools, currently only including the authenticate method

**authenticate**
- Main entry point for OAuth flow
- Checks for existing tokens or authorization codes
- Initiates new OAuth flow if necessary

**_start_oauth_flow**
- Generates the OAuth authorization URL
- Returns an OAuthFlowResult object with the authorization URL and tool name

**_exchange_code_for_token**
- Exchanges an authorization code for an access token
- Stores the received token in the run context

### Helper Methods
**_get_secret**
- Retrieves secrets from environment variables or a secrets database

**_get_extra_auth_params**
- Placeholder for adding additional authorization parameters in subclasses

**_get_extra_token_data**
- Placeholder for adding additional token exchange data in subclasses

**_handle_token_response**
- Placeholder for handling additional token response data in subclasses

### Dependencies
- dataclasses
- typing
- urllib.parse
- os
- dotenv
- httpx
- agentic.common
- agentic.events
- agentic.tools.base

This tool provides a flexible base for implementing OAuth flows, with hooks for customization in specific OAuth provider implementations. It handles the core OAuth logic while allowing for extension and modification as needed.

---



# Playwright

Playwright is a browser automation tool implemented in Python. It provides a set of functions for interacting with web pages, including navigation, content extraction, and element manipulation. This tool is designed to facilitate web scraping, testing, and automation tasks.

## Key Features
- Browser automation using Chromium
- Headless and visible browser modes
- Navigation to URLs
- Text extraction from web pages
- Screenshot capture
- Element interaction (clicking)
- Batch download of multiple pages

## Main Functions

### Navigation
**navigate_to_url(run_context, url)**
- Navigates to the specified URL and returns the page title
- Handles timeouts and exceptions

### Content Extraction
**extract_text(run_context, selector, convert_to_markdown=True)**
- Extracts text content from elements matching a CSS selector
- Option to convert HTML content to Markdown format

### Screenshot
**take_screenshot(run_context, selector=None, filename=None)**
- Captures a screenshot of the entire page or a specific element
- Allows specifying a custom filename or uses a timestamp-based name

### Element Interaction
**click_element(run_context, selector)**
- Clicks an element on the page matching the provided CSS selector

### Batch Operations
**download_pages(run_context, pages)**
- Downloads content from multiple pages in a batch
- Returns a list of tuples containing URL, title, and content for each page

## Usage Notes
- Requires installation of the playwright package: `pip install playwright`
- After installation, run: `playwright install chromium` to set up the browser
- The tool can be initialized with a headless mode option (default is visible browser)
- Browser resources are automatically cleaned up when the tool instance is deleted
- The html2text module is required for Markdown conversion in the extract_text function
- Error handling is implemented for most functions, returning descriptive error messages
- The tool maintains a single browser instance across multiple operations for efficiency
- The download_pages function opens and closes the browser for each batch of pages

---


# Rag Tool
A tool for managing and querying knowledge bases using Retrieval-Augmented Generation (RAG). It provides functionality for indexing, searching, and retrieving content from a vector database (Weaviate).

## Key Features
- Index and store content (text or files) in a knowledge base
- Search the knowledge base for relevant information
- List documents in the knowledge base
- Retrieve full documents from the knowledge base

## Main Functions

### Content Management
**save_content_to_knowledge_index**
- Saves content (text or file) to a specified knowledge index
- Handles document updates and duplicates
- Generates document summaries and embeddings

### Search and Retrieval
**search_knowledge_index**
- Searches the knowledge index for relevant documents based on a query
- Supports vector and hybrid (vector + keyword) search
- Returns matching documents with metadata

**review_full_document**
- Retrieves and reconstructs a full document from the knowledge base

### Index Management
**list_documents**
- Lists all documents stored in the knowledge index

## Usage Notes
- The tool uses Weaviate as the vector database for storing and querying embeddings
- It requires external dependencies for embedding generation, text chunking, and summarization
- The default index name is "knowledge_base" but can be customized
- The tool supports indexing multiple files on initialization using file paths or glob patterns
- Error handling is implemented for most operations, with informative error messages returned
- The tool uses the "BAAI/bge-small-en-v1.5" model for generating embeddings
- Document summaries are generated using the "openai/gpt-4o-mini" model
- The `list_indexes` method is commented out in the `get_tools` function and not available for use

---


# Rest Api Tool
The Rest Api Tool is a Python-based utility for making HTTP requests to RESTful APIs. It provides a flexible interface for authentication, header management, and various HTTP methods, allowing users to interact with APIs easily and efficiently.

## Key Features
- Asynchronous HTTP requests using httpx
- Support for multiple authentication methods (Basic, Bearer Token, Custom Parameter)
- Custom header management
- Handling of various response types (JSON, Image, HTML, Plain Text, CSV, XML)
- Optional conversion of JSON responses to Pandas DataFrames
- Debugging capabilities for request configurations

## Main Functions

### Authentication and Configuration
**prepare_auth_config**
- Constructs an authentication configuration for use in subsequent requests
- Supports Basic Auth, Bearer Token, Custom Parameter, and No Auth options
- Returns a unique identifier for the created auth configuration

**add_request_header**
- Adds a custom header to an existing auth configuration

**debug_request**
- Returns debug information about a specific request configuration

### HTTP Methods
**get_resource**
- Performs a GET request to the specified URL
- Supports query parameters and authentication

**post_resource**
- Performs a POST request to the specified URL
- Supports JSON and form data payloads
- Handles content type specification

**put_resource**
- Performs a PUT request to the specified URL
- Supports JSON payload

**patch_resource**
- Performs a PATCH request to the specified URL
- Supports JSON payload

**delete_resource**
- Performs a DELETE request to the specified URL

## Usage Notes
- The tool uses asyncio for asynchronous operations, so it should be used in an async context
- Authentication configurations must be prepared before making authenticated requests
- The tool can handle various response types, including JSON, images, HTML, plain text, CSV, and XML
- JSON responses can optionally be converted to Pandas DataFrames
- Image responses are processed and uploaded to an S3 bucket, returning a markdown-formatted image link
- The tool depends on external libraries such as httpx, Pillow, and pandas
- Error handling is implemented for HTTP status codes 400 and above
- The tool is designed to be used within a larger framework that provides a RunContext for logging and secret management

---


# Scaleserp Browser
Scaleserp Browser is a tool designed to search the web and retrieve page contents using the SCALESERP API. It provides functionality to perform web searches, download web pages, and extract text content from HTML pages.

## Key Features
- Web searching using SCALESERP API
- Fallback to ScrapingBee API if SCALESERP times out
- Downloading and processing of web pages
- HTML to text conversion for easier content reading
- Asynchronous operations for improved performance

## Main Functions

### Web Browsing
**browse_web_tool**
- Performs a web search using the SCALESERP API based on the provided search term
- Retrieves and processes the top search results
- Falls back to ScrapingBee API if SCALESERP times out
- Returns concatenated text content from the searched pages

### Web Page Downloading
**download_web_pages**
- Downloads and processes multiple web pages based on provided URLs
- Extracts text content from HTML pages
- Returns concatenated text content from the downloaded pages

## Usage Notes
- Requires a SCALESERP API key set in the environment variable "SCALESERP_API_KEY"
- Optionally uses a ScrapingBee API key set in the environment variable "SCRAPINGBEE_API_KEY" for fallback
- Implements asynchronous operations for improved performance when downloading multiple pages
- Uses html2text library to convert HTML content to readable text
- Has a maximum content limit of 10,000 characters per search or download operation
- Handles various errors and exceptions during web requests and content processing

---


# Tavily Search Tool
The Tavily Search Tool is a Python-based utility that interfaces with the Tavily API to perform web searches, query news, and download web page content. It provides a set of asynchronous functions to interact with Tavily's search and extraction capabilities.

## Key Features
- Perform web searches with customizable parameters
- Query for recent news articles on specific topics
- Download and extract content from specified web pages
- Asynchronous operations for efficient API interactions
- Integration with a RunContext for managing API keys securely

## Main Functions

**Web Search Functions**

`perform_web_search`
- Conducts a web search using the Tavily search engine
- Returns a list of search results, including page details and optionally images

`query_for_news`
- Retrieves the latest news headlines on a given topic
- Returns results as a pandas DataFrame

**Content Extraction**

`tavily_download_pages`
- Downloads and extracts content from one or more specified URLs
- Returns the extracted content as JSON data

## Usage Notes
- An API key for Tavily is required to use this tool
- The tool uses asynchronous HTTP requests, requiring an asynchronous runtime
- The `RunContext` object is used to manage and retrieve the API key securely
- Search results can include images and full page contents based on function parameters
- The tool provides options to include or exclude specific domains in search results
- There's a built-in function to deduplicate and format search results, but it's not directly exposed as a tool

---


# Text To Speech Tool

This tool converts text to speech using OpenAI's Text-to-Speech API. It can process both direct text input and text from files, generating audio files with various voice options.

## Key Features
- Convert text to speech using OpenAI's TTS API
- Support for multiple voice options (alloy, echo, fable, onyx, nova, shimmer)
- Ability to process long texts by splitting into chunks
- Generation of MP3 audio files from input text
- Handling of both direct text input and text from files

## Main Functions

**Text-to-Speech Conversion**
generate_speech_file_from_text
- Converts given text or text from an input file to speech
- Supports various voice options
- Handles long texts by splitting into manageable chunks
- Generates and saves an MP3 audio file
- Returns a JSON string with the local file path of the generated audio

## Usage Notes
- Requires an OpenAI API key to be set in the configuration
- Depends on the `pydub` library (version 0.25.1) for audio processing
- The tool is designed to work within a specific runtime context that provides methods for file uploading and URL generation (currently commented out in the code)
- Generated audio files are saved locally with a timestamp in the filename
- The tool can handle long texts by splitting them into chunks of 4096 characters maximum
- Error handling is implemented, with error messages returned as JSON strings
- The actual S3 upload functionality is currently commented out in the code

Note: The current implementation saves files locally instead of uploading to S3 as the relevant methods are commented out. The returned URL is a local file path.

---


# Unit Test Tool
The Unit Test Tool is a custom tool designed for testing purposes within a larger framework. It provides various functions to simulate different scenarios and behaviors, primarily for unit testing and debugging.

## Key Features
- File operations for maintaining and reading a state file
- Simulated time delays
- Asynchronous function testing
- Logging capabilities
- Story log reading

## Main Functions

### File Operations
**cleanup_state_file**
- Removes the state file if it exists

**read_state_file**
- Reads and returns the contents of the state file

### Time Management
**sleep_for_time**
- Pauses execution for a specified number of seconds

### Asynchronous Operations
**test_using_async_call**
- Simulates an asynchronous operation with a 1-second delay

**read_story_log**
- Asynchronously reads and returns the content of the story log

### Logging Functions
**sync_function_with_logging**
- Demonstrates synchronous logging to the run context

**sync_function_direct_logging**
- Illustrates synchronous logging using yield

**async_function_with_logging**
- Showcases asynchronous logging to the run context

## Usage Notes
- The tool uses a state file named "test_state.txt" for some operations
- A story log file path can be specified during initialization
- Some functions require a RunContext object for logging
- The tool includes both synchronous and asynchronous functions
- Asynchronous functions should be called with appropriate async/await syntax
- The get_tools method returns a list of all available tool functions

---


# Weather Tool

A versatile tool for retrieving various types of weather information including current conditions, forecasts, historical data, and historical averages. It utilizes the Open-Meteo API to fetch weather data for specified locations.

## Key Features
- Get current weather conditions for a specific location
- Retrieve hourly or daily weather forecasts
- Access historical weather data for a given date range
- Calculate historical weather averages for specific dates across multiple years

## Main Functions

### Current Weather
**get_current_weather**
- Retrieves current weather conditions for a specified location
- Provides detailed information including temperature, wind, precipitation, and more

### Weather Forecast
**get_forecast_weather**
- Fetches weather forecasts for a specified location
- Offers both hourly (7 days) and daily (16 days) forecast options
- Includes temperature, precipitation, wind, and other relevant weather data

### Historical Weather
**get_historical_weather**
- Retrieves historical weather data for a specific location and date range
- Provides daily weather information including temperature, precipitation, wind, and more

### Historical Averages
**get_historical_averages**
- Calculates 5-year historical weather averages for a specific date range
- Allows for mean or median averaging methods
- Provides averaged data for temperature, precipitation, wind, and other weather parameters

## Usage Notes
- The tool uses latitude and longitude for location specification
- Temperature units can be set to either Fahrenheit or Celsius
- Historical data and averages require date inputs in specific formats
- Some functions may require an API key for professional or production use
- The tool handles data retrieval errors and provides informative error messages
- Maximum date range for historical averages is configurable (default 14 days)
- The tool automatically handles timezone differences and provides formatted datetime information

This Weather Tool offers a comprehensive set of functions for various weather-related queries, making it suitable for a wide range of applications requiring current, forecasted, or historical weather data.

---

