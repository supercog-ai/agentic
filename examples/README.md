# Agentic Agents Documentation

This document provides documentation for all available agents in the Agentic framework.

## Table of Contents

- [Agentic Oracle](#agentic-oracle)
- [Airbnb Calendar Agent](#airbnb-calendar-agent)
- [Basic Agent](#basic-agent)
- [Database Agent](#database-agent)
- [Dynamic Tools Agent](#dynamic-tools-agent)
- [Firecrawl Agent](#firecrawl-agent)
- [Github](#github)
- [March Madness](#march-madness)
- [Meeting Notetaker](#meeting-notetaker)
- [News Demo](#news-demo)
- [Oss Deep Research](#oss-deep-research)
- [Oss Operator](#oss-operator)
- [People Researcher](#people-researcher)
- [Podcast](#podcast)
- [Rag Agent](#rag-agent)
- [Sequential Thinking Agent](#sequential-thinking-agent)
- [Standup Agent](#standup-agent)
- [Tool Builder](#tool-builder)
- [Weather Agent](#weather-agent)

---

## [Agentic Oracle](https://github.com/supercog-ai/agentic/blob/main/examples/agentic_oracle.py)
Agentic Oracle is an AI agent designed to assist users in building other agents and answering questions about the Agentic framework. It utilizes a Retrieval-Augmented Generation (RAG) approach to access and provide information from the Agentic documentation.

### Tools:
- **[RAGTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/rag_tool.py)** - Manages a knowledge base using vector search, allowing the agent to retrieve relevant information from indexed documents. It's pre-populated with Agentic documentation.

### API Keys required:
- LLM token (OpenAI, Anthropic, etc.)
- Depending on the underlying vector database used by RAGTool, additional API keys may be required (e.g., Weaviate, Pinecone)

---


## [Airbnb Calendar Agent](https://github.com/supercog-ai/agentic/blob/main/examples/airbnb_calendar_agent.py)
The Airbnb Calendar Agent is an AI assistant designed to help users interact with their Airbnb calendar data. It provides functionality to check availability, view upcoming bookings, get booking statistics, and retrieve blocked dates from an Airbnb calendar.

### Tools:
- **[Airbnb Calendar Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/airbnb_calendar_tool.py)** - Provides functions to interact with Airbnb calendar data, including listing events, checking availability, getting booking statistics, and retrieving blocked dates.

### API Keys required:
- LLM token (OpenAI)
- Airbnb calendar URL (set as AIRBNB_CALENDAR_URL in the environment or secrets)

---


## [Basic Agent](https://github.com/supercog-ai/agentic/blob/main/examples/basic_agent.py)
This is a simple agent designed to answer weather-related questions. It utilizes the WeatherTool to provide weather information for specified locations. The agent can respond to predefined prompts about weather in New York City and Los Angeles, as well as handle user queries in an interactive REPL loop.

### Tools:
- **[WeatherTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/weather_tool.py)** - Retrieves weather information using the Open-Meteo API, including current conditions, forecasts, and historical data.

### API Keys required:
- LLM token (OpenAI or local model like LMStudio)
- No additional API keys are required for the WeatherTool as it uses the free tier of the Open-Meteo API

---


## [Database Agent](https://github.com/supercog-ai/agentic/blob/main/examples/database/database_agent.py)
This is a simple Text-to-SQL agent that uses a database tool to answer questions. It acts as a helpful data analyst, utilizing the provided database connection to query and retrieve information based on user input.

### Tools:
- **[Database Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/database_tool.py)** - Connects to and queries a SQLite database to retrieve information based on SQL queries

### API Keys required:
- None

---


## [Dynamic Tools Agent](https://github.com/supercog-ai/agentic/blob/main/examples/dynamic_tools_agent.py)
This agent demonstrates dynamic tool use, allowing tools to be added and enabled on-demand. It uses the AutomaticTools meta-tool to manage a set of pre-configured tools that can be searched for and enabled as needed. The agent can list available tools and enable them for different purposes based on user requests.

### Tools:
- **[AutomaticTools](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/automatic_tools.py)** - A meta-tool that manages a set of tools, allowing for dynamic tool discovery and enabling.
- **[GoogleNewsTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/google_news.py)** - Retrieves and analyzes news articles from Google News.
- **[WeatherTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/weather_tool.py)** - Provides weather information including current conditions, forecasts, and historical data.
- **[DatabaseTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/database_tool.py)** - Allows interaction with SQL databases for querying and managing data.
- **[LinkedinDataTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/linkedin_tool.py)** - Retrieves LinkedIn profile and company information using the RapidAPI LinkedIn Data API.
- **[ImageGeneratorTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/image_generator.py)** - Generates images based on text prompts using OpenAI's GPT-4V model.
- **[TavilySearchTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/tavily_search_tool.py)** - Performs web searches and retrieves content using the Tavily API.
- **[IMAPTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/imap_tool.py)** - Manages email operations using the IMAP protocol, focusing on Gmail integration.
- **[DuckDuckGoTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/duckduckgo.py)** - Performs web searches using the DuckDuckGo search engine.
- **[ShellTool](https://github.com/langchain-ai/langchain/blob/master/libs/community/langchain_community/tools/shell/tool.py)** - Executes shell commands (loaded from LangChain).

### API Keys required:
- LLM token (OpenAI)
- RapidAPI key (for LinkedinDataTool)
- OpenAI API key (for ImageGeneratorTool)
- Tavily API key (for TavilySearchTool)
- Gmail account credentials (for IMAPTool)

---


## [Firecrawl Agent](https://github.com/supercog-ai/agentic/blob/main/examples/learning/firecrawl_agent.py)
The Firecrawl Agent is a web research assistant powered by Firecrawl. It utilizes the Firecrawl MCP (Model Control Protocol) tool to crawl and analyze web content, extract relevant information, follow links, explore related content, and summarize findings. The agent is designed to respect website terms of service and robots.txt files while conducting web research.

### Tools:
- **[MCPTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/mcp_tool.py)** - A universal wrapper for MCP (Model Control Protocol) tools that can work with any MCP server. In this case, it's used to interface with Firecrawl for web crawling and analysis.

### API Keys required:
- LLM token (OpenAI GPT-4)
- Firecrawl API key

---


## [Github](https://github.com/supercog-ai/agentic/blob/main/examples/github.py)
This agent is designed to interact with GitHub repositories. It can perform various GitHub-related tasks such as searching repositories, creating issues, and creating pull requests. The agent uses natural language processing to understand user queries and leverages the GithubTool to execute GitHub operations.

### Tools:
- **[GithubTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/github_tool.py)** - Provides functionality to interact with GitHub's API, including repository management, issue handling, and pull request operations.

### API Keys required:
- LLM token (Anthropic's Claude API key)
- GitHub API credentials (OAuth token or personal access token)

---


## [March Madness](https://github.com/supercog-ai/agentic/blob/main/examples/march_madness.py)
The March Madness agent is designed to predict the outcome of the NCAA basketball tournament. It analyzes team statistics, generates matchups, predicts winners for each game, and builds a complete tournament bracket prediction.

### Tools:
- **[TavilySearchTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/tavily_search_tool.py)** - Performs web searches using the Tavily API to gather information about basketball teams and tournament data

### API Keys required:
- LLM token (OpenAI for GPT-4, Anthropic for Claude)
- TAVILY_API_KEY

---


## [Meeting Notetaker](https://github.com/supercog-ai/agentic/blob/main/examples/meeting_notetaker.py)
This agent manages meetings, including joining new meetings, retrieving meeting information, summaries and transcripts, listing existing meetings, and checking meeting status. It uses the MeetingBaasTool to interact with a meeting management system.

### Tools:
- **[MeetingBaasTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/meeting_tool.py)** - Provides functionality for joining meetings, retrieving meeting information, summaries and transcripts, listing meetings, and checking meeting status.

### API Keys required:
- LLM token (OpenAI)
- [MeetingBaaS API key](https://meetingbaas.com/) (required by MeetingBaasTool)

This documentation reflects the actual implemented functionality in the provided code for the Meeting Notetaker agent.

---


## [News Demo](https://github.com/supercog-ai/agentic/blob/main/examples/news_demo.py)
This agent demonstrates a simple news reporting system using a producer-reporter model. The producer interacts with a human to get a news topic, then instructs a reporter to fetch and summarize news on that topic using Google News.

### Tools:
- **[Google News](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/google_news.py)** - Retrieves news articles from Google News based on a specified topic
- **[LinkedIn Data](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/linkedin_tool.py)** - Searches for LinkedIn profiles and retrieves profile information (Note: This tool is imported but not used in the main agent functionality)

### API Keys required:
- LLM token (OpenAI)
- RapidAPI key (for LinkedIn Data Tool, if used)

---


## [Oss Deep Research](https://github.com/supercog-ai/agentic/blob/main/examples/deep_research/oss_deep_research.py)
Oss Deep Research is an AI agent designed to conduct in-depth research on a given topic. It generates a structured report by planning sections, performing web searches, and writing content for each section. The agent uses a multi-step process involving several sub-agents to create a comprehensive and well-researched report.

### Tools:
- **[Tavily Search Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/tavily_search_tool.py)** - Performs web searches using the Tavily API to gather information for the report
- **[Playwright Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/playwright.py)** - Used as a fallback to download web pages when Tavily search results are incomplete

### API Keys required:
- LLM token (OpenAI, Anthropic, etc.)
- TAVILY_API_KEY

---


## [Oss Operator](https://github.com/supercog-ai/agentic/blob/main/examples/oss_operator.py)
This agent is designed to perform web browsing tasks using the BrowserUseTool, which utilizes the browser-use agent for automated interactions with a real browser. It can execute various web-based tasks as instructed by the user.

### Tools:
- **[BrowserUseTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/browser_use.py)** - Automates browser interactions using Playwright and an LLM vision model. It can navigate websites, perform actions, and extract information from web pages.

### API Keys required:
- LLM token (OpenAI or Google, depending on the chosen model)
- Browser-use API key (if required by the browser-use package)

The agent is configured to use the OpenAI GPT-4 model by default, but it includes commented options for using Gemini 2.0 Flash or GPT-4o-mini. The BrowserUseTool is set up to use the Gemini 2.0 Flash model for its operations.

This agent can optionally use the user's existing Chrome browser instance by specifying the Chrome executable path.

To run this agent, you need to install the following packages:
- playwright
- browser-use

The agent operates in a REPL loop, allowing for interactive task assignment and execution of web browsing operations.

---


## [People Researcher](https://github.com/supercog-ai/agentic/blob/main/examples/people_researcher.py)
The People Researcher is an AI agent designed to gather and analyze information about individuals using LinkedIn data. It searches for LinkedIn profiles, interacts with users to confirm the correct profile, and generates detailed reports on individuals and their associated companies.

### Tools:
- **[LinkedIn Data Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/linkedin_tool.py)** - Provides functions to search LinkedIn profiles, retrieve profile information, and get company details using the RapidAPI LinkedIn Data API.

### API Keys required:
- LLM token (OpenAI)
- RapidAPI key for LinkedIn Data API (set as RAPIDAPI_KEY environment variable)

The People Researcher agent utilizes a combination of LinkedIn data retrieval and natural language processing to conduct research on individuals. It incorporates two main components:

1. The main "Person Researcher" agent, which handles user interactions, LinkedIn profile searches, and orchestrates the research process.
2. A sub-agent called "Person Report Writer," which generates detailed reports on individuals and their companies.

The agent workflow includes:
1. Accepting a name and optionally a company name from the user
2. Searching for matching LinkedIn profiles
3. Interacting with the user to confirm the correct profile if multiple matches are found
4. Generating a comprehensive report on the selected individual, including their career progression and company information

The agent uses asynchronous functions for API calls, wrapped in a synchronous interface for easier integration. It also includes a function to pause for user input when clarification is needed.

This agent is designed to run in a REPL (Read-Eval-Print Loop) environment, allowing for interactive sessions with users.

---


## [Podcast](https://github.com/supercog-ai/agentic/blob/main/examples/podcast.py)
This agent is designed to produce a daily news podcast. It utilizes multiple specialized agents for collecting news from different domains (general AI news, sports, and finance) and then processes this information to create a podcast episode. The agent can generate audio content and interact with the Transistor.fm API to manage podcast episodes.

### Tools:
- **[GoogleNewsTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/google_news.py)** - Retrieves news articles from Google News for various topics and categories
- **[TavilySearchTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/tavily_search_tool.py)** - Performs web searches and retrieves relevant information using the Tavily API
- **[TextToSpeechTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/text_to_speech_tool.py)** - Converts text to speech using OpenAI's Text-to-Speech API
- **[AuthorizedRestApiTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/auth_rest_api_tool.py)** - Provides authenticated access to REST APIs, used here for interacting with the Transistor.fm API

### API Keys required:
- LLM token (OpenAI for GPT-4O, Anthropic for Claude)
- Google News API key (for GoogleNewsTool)
- Tavily API key (for TavilySearchTool)
- OpenAI API key (for TextToSpeechTool)
- Transistor.fm API key (for AuthorizedRestApiTool)

---


## [Rag Agent](https://github.com/supercog-ai/agentic/blob/main/examples/learning/rag_agent.py)
This agent utilizes a Retrieval-Augmented Generation (RAG) tool to answer questions based on a specific knowledge base. It is designed to retrieve information from a pre-populated index containing content from a specified web page before responding to queries.

### Tools:
- **[RAG Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/rag_tool.py)** - Manages a knowledge index for retrieval and querying of information. It is initialized with a default index and pre-populated with content from a specified URL.

### API Keys required:
- LLM token (OpenAI, Anthropic, etc.) for the underlying language model used by the Agent
- Any API keys required by the RAG Tool for indexing and querying (e.g., vector database API key if applicable)

---


## [Sequential Thinking Agent](https://github.com/supercog-ai/agentic/blob/main/examples/learning/sequential_thinking_agent.py)
This agent utilizes the Sequential Thinking MCP (Model Control Protocol) tool to break down complex problems into manageable steps. It employs a structured approach to problem-solving, encouraging careful consideration of each step and potential alternative approaches.

### Tools:
- **[MCPTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/mcp_tool.py)** - A universal wrapper for MCP tools that works with any MCP server. In this case, it's used to initialize and interact with the Sequential Thinking MCP.

### API Keys required:
- LLM token (OpenAI)

The Sequential Thinking Agent is designed to assist users in breaking down complex problems into smaller, more manageable steps. It uses the Sequential Thinking MCP tool to structure its approach to problem-solving. The agent is instructed to:

1. Break down complex problems into smaller steps
2. Think through each step carefully
3. Revise thinking if needed
4. Consider alternative approaches

The agent uses the GPT-4 model from OpenAI for generating responses and interacts with users through a REPL (Read-Eval-Print Loop) interface.

---


## [Standup Agent](https://github.com/supercog-ai/agentic/blob/main/examples/standup_agent.py)
The Standup Agent is an AI assistant designed to prepare for and assist with development standup meetings. It retrieves information about open pull requests, including reviews and comments, and provides a summary of commits made in the last week. The agent uses the GitHub API to gather this data and can interact with users through a REPL interface.

### Tools:
- **[Github Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/github_tool.py)** - Interacts with the GitHub API to retrieve information about repositories, pull requests, and commits.

### API Keys required:
- LLM token (OpenAI)
- GitHub API key

---


## [Tool Builder](https://github.com/supercog-ai/agentic/blob/main/examples/tool_builder.py)
Tool Builder is an AI agent designed to assist users in creating new AI agent tools. It guides users through the process of defining, designing, and coding custom tools that can extend the capabilities of AI agents.

### Tools:
This agent does not use any additional tools.

### API Keys required:
- LLM token (Anthropic Claude)

The Tool Builder agent uses the Claude language model from Anthropic to interact with users and generate tool code. It does not directly use any other external APIs or tools. The agent's primary function is to facilitate the creation of new tools through a conversational interface, leveraging its understanding of tool structure and design patterns.

---


## [Weather Agent](https://github.com/supercog-ai/agentic/blob/main/examples/learning/weather_agent.py)
This is a simple "hello world" agent example that provides a basic weather response. The agent uses a fake weather function to demonstrate the basic structure of an agent without actually connecting to a real weather API.

### Tools:
- **[weather_tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/weather_tool.py)** - A simple function that returns a static weather message: "The weather is nice today."

### API Keys required:
- LLM token (OpenAI)

The Weather Agent is a basic example that demonstrates the structure of an agent using the Agentic framework. It uses a single tool (weather_tool) which provides a static weather response. The agent is configured to use the "openai/gpt-4o-mini" model for natural language processing. 

The agent is designed to engage in a REPL (Read-Eval-Print Loop) conversation, where it can respond to user queries about the weather using its simple weather tool. While the weather information is not real or dynamic, this example serves as a starting point for understanding how to create more complex agents with actual API integrations.

---

