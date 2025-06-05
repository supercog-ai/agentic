# Agentic Agents Documentation

This document provides documentation for all available agents in the Agentic framework.

## Table of Contents

- [Agentic Oracle](#agentic-oracle)
- [Airbnb Calendar Agent](#airbnb-calendar-agent)
- [Basic Agent](#basic-agent)
- [Database Agent](#database-agent)
- [Debugger](#debugger)
- [Dynamic Tools Agent](#dynamic-tools-agent)
- [Firecrawl Agent](#firecrawl-agent)
- [Github](#github)
- [Handoff Demo](#handoff-demo)
- [Human In The Loop](#human-in-the-loop)
- [March Madness](#march-madness)
- [Meeting Notetaker](#meeting-notetaker)
- [News Demo](#news-demo)
- [Oss Deep Research](#oss-deep-research)
- [Oss Operator](#oss-operator)
- [People Researcher](#people-researcher)
- [Podcast Long](#podcast-long)
- [Podcast Short](#podcast-short)
- [Rag Agent](#rag-agent)
- [Sequential Thinking Agent](#sequential-thinking-agent)
- [Standup Agent](#standup-agent)
- [Testing](#testing)
- [Tool Builder](#tool-builder)
- [Weather Agent](#weather-agent)

---

## [Agentic Oracle](https://github.com/supercog-ai/agentic/blob/main/examples/agentic_oracle.py)
This agent is designed to help answer questions about the Agentic framework and assist in building new agents. It utilizes a RAG (Retrieval-Augmented Generation) tool to access and search a knowledge base containing Agentic documentation.

### Tools:
- **[RAGTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/rag_tool.py)** - Provides functionality for indexing, searching, and retrieving content from a vector database. Used here to access Agentic documentation.

### API Keys required:
- LLM token (OpenAI, Anthropic, etc.) - Required for the Agent's language model
- No additional API keys are required for the RAG tool as implemented

---

## [Airbnb Calendar Agent](https://github.com/supercog-ai/agentic/blob/main/examples/airbnb_calendar_agent.py)
This agent is an Airbnb Calendar Assistant that helps users interact with their Airbnb calendar data. It can check availability, view upcoming bookings, get booking statistics, and find blocked dates within specified date ranges.

### Tools:
- **[Airbnb Calendar Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/airbnb_calendar_tool.py)** - Provides functions to interact with Airbnb calendar data, including listing events, checking availability, getting booking statistics, and retrieving blocked dates.

### API Keys required:
- LLM token (OpenAI API key for gpt-4o-mini model)
- AIRBNB_CALENDAR_URL (URL for the Airbnb calendar iCal feed, set in the thread context)

---

## [Basic Agent](https://github.com/supercog-ai/agentic/blob/main/examples/basic_agent.py)
This is a simple weather reporting agent that can answer questions about current weather conditions in different cities. It uses the WeatherTool to retrieve weather data and responds to user queries about the weather in specific locations.

### Tools:
- **[WeatherTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/weather_tool.py)** - Retrieves current weather conditions for specified locations using the Open-Meteo API

### API Keys required:
- LLM token (OpenAI for GPT-4O-MINI, or local setup for LMSTUDIO_QWEN)
- No additional API keys required for the WeatherTool

---

## [Database Agent](https://github.com/supercog-ai/agentic/blob/main/examples/database/database_agent.py)
This agent is a simple Text-to-SQL agent designed to act as a helpful data analyst. It uses a database tool to answer questions by querying an SQLite database.

### Tools:
- **[DatabaseTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/database_tool.py)** - Connects to and queries an SQLite database to retrieve information based on user questions

### API Keys required:
- None

---

## [Debugger](https://github.com/supercog-ai/agentic/blob/main/examples/debugger.py)
This is a simple Text-to-SQL agent designed to query a SQLite database named "Threads". It uses a database tool to answer questions and includes a browser automation tool for potential web-related tasks.

### Tools:
- **[DatabaseTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/database_tool.py)** - Provides functionality to interact with and query a SQLite database
- **[PlaywrightTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/playwright_tool.py)** - Offers browser automation capabilities using Playwright

### API Keys required:
- No specific API keys are required for this agent based on the tools used

---

## [Dynamic Tools Agent](https://github.com/supercog-ai/agentic/blob/main/examples/dynamic_tools_agent.py)
This agent demonstrates dynamic tool use, allowing tools to be added and enabled on-demand. It uses the AutomaticTools meta-tool to manage a list of configurable tools that can be searched for and enabled as needed.

### Tools:
- **AutomaticTools** - A meta-tool that manages a list of configurable tools, allowing the agent to search for and enable tools dynamically.
- **GoogleNewsTool** - Retrieves and analyzes news articles from Google News.
- **WeatherTool** - Provides weather information including current conditions, forecasts, and historical data.
- **DatabaseTool** - Interacts with SQL databases, executing queries and managing database operations.
- **LinkedinDataTool** - Retrieves and searches LinkedIn data using the RapidAPI LinkedIn Data API.
- **ImageGeneratorTool** - Generates images based on text prompts using OpenAI's GPT-4V model.
- **TavilySearchTool** - Performs web searches and content extraction using the Tavily API.
- **IMAPTool** - Accesses and manages email inboxes using the IMAP protocol, focusing on Gmail integration.
- **DuckDuckGoTool** - Performs web searches using the DuckDuckGo search engine.
- **ShellTool** - A LangChain tool for executing shell commands (loaded from the tool registry).

### API Keys required:
- LLM token (OpenAI API key for GPT-4O-MINI model)
- Google News API key (for GoogleNewsTool)
- OpenAI API key (for ImageGeneratorTool)
- Tavily API key (for TavilySearchTool)
- RapidAPI key (for LinkedinDataTool)
- Gmail credentials (for IMAPTool)

---

## [Firecrawl Agent](https://github.com/supercog-ai/agentic/blob/main/examples/learning/firecrawl_agent.py)
This agent is designed to crawl and analyze web content using Firecrawl. It acts as a web research assistant, capable of extracting relevant information, exploring related content, and summarizing findings while respecting website terms of service and robots.txt files.

### Tools:
- **[MCPTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/mcp_tool.py)** - A universal wrapper for MCP (Model Control Protocol) tools that can work with any MCP server. In this case, it's used to interface with Firecrawl for web crawling and analysis.

### API Keys required:
- LLM token (OpenAI GPT-4)
- Firecrawl API key (set as FIRECRAWL_API_KEY in the environment variables)

---

## [Github](https://github.com/supercog-ai/agentic/blob/main/examples/github.py)
This agent is designed to interact with GitHub repositories. It can perform various GitHub operations such as searching repositories, creating issues, and creating pull requests. The agent uses natural language processing to understand user queries and leverages the GithubTool to execute GitHub-related tasks.

### Tools:
- **[GithubTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/github.py)** - Provides functionality to interact with GitHub's API, including repository management, issue handling, and pull request creation.

### API Keys required:
- LLM token (OpenAI)
- GitHub API credentials (API key or OAuth token)

---

## [Handoff Demo](https://github.com/supercog-ai/agentic/blob/main/examples/learning/handoff_demo.py)
This agent demonstrates the use of the handoff functionality to coordinate between two agents. The main "Producer" agent prints messages and hands off control to a secondary "Agent B", then prints a final message after Agent B completes.

### Tools:
- **[Handoff](https://github.com/supercog-ai/agentic/blob/5fa8e0a3ab25e838ae62862f280849a40ce1e032/src/agentic/actor_agents.py#L839C1-L840C1)** - Allows an agent to transfer control to another agent, execute its instructions, and then resume control

### API Keys required:
- LLM token (OpenAI)

---

## [Human In The Loop](https://github.com/supercog-ai/agentic/blob/main/examples/learning/human_in_the_loop.py)
This agent acts as a news researcher, querying Google News for a given topic. If the topic is unknown, it will prompt the user for input before searching for news on that topic.

### Tools:
- **[Google News Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/google_news.py)** - Retrieves news articles from Google News based on a specified topic
- **[Human Interrupt Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/human_interrupt.py)** - Allows for human interruption and input during the agent's execution

### API Keys required:
- None specified in the provided code

---

## [March Madness](https://github.com/supercog-ai/agentic/blob/main/examples/march_madness.py)
This agent predicts outcomes for the NCAA March Madness basketball tournament. It analyzes team statistics, predicts matchups, and generates a complete tournament bracket prediction.

### Tools:
- **[Tavily Search Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/tavily_search_tool.py)** - Performs web searches using the Tavily API to gather information about basketball teams and tournament details

### API Keys required:
- LLM token (OpenAI for GPT-4, Anthropic for Claude)
- TAVILY_API_KEY

---

## [Meeting Notetaker](https://github.com/supercog-ai/agentic/blob/main/examples/meeting_notetaker.py)
This agent acts as a Meeting Manager that can help join meetings, retrieve transcripts and summaries, and provide information about meetings. It uses the MeetingBaasTool to join meeting, get meeting data etc.

### Tools:
- **[MeetingBaasTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/meeting_tool.py)** - Provides functionality to join meetings, get transcripts, summaries, and meeting information.

### API Keys required:
- LLM token (OpenAI)
- MeetingBaaS API key (required by MeetingBaasTool. You can get the API from [MeetingBAAS](https://meetingbaas.com/))

---

## [News Demo](https://github.com/supercog-ai/agentic/blob/main/examples/news_demo.py)
This agent demonstrates a news reporting system with a producer and reporter. The producer interacts with a human to get a news topic, then instructs the reporter to fetch news headlines on that topic using Google News. The producer then summarizes the report in one sentence.

### Tools:
- **[Google News](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/google_news.py)** - Retrieves news articles from Google News based on specified topics or queries

### API Keys required:
- LLM token (OpenAI)
- No additional API keys are required for the Google News tool

---

## [Oss Deep Research](https://github.com/supercog-ai/agentic/blob/main/examples/deep_research/oss_deep_research.py)
An AI agent that performs in-depth research on a given topic, generating a comprehensive report with multiple sections. It uses web searches, content extraction, and AI-powered writing to create detailed and well-structured reports.

### Tools:
- **[Tavily Search Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/tavily_search_tool.py)** - Performs web searches and retrieves content using the Tavily API
- **[Playwright Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/playwright.py)** - Downloads web pages and extracts content using browser automation (used as a fallback)

### API Keys required:
- LLM token (OpenAI, Anthropic, etc.)
- [TAVILY_API_KEY](https://tavily.com/)

---

## [Oss Operator](https://github.com/supercog-ai/agentic/blob/main/examples/oss_operator.py)
This agent is designed to perform web browsing tasks using the browser-use agent. It utilizes a real browser instance through Playwright and an LLM vision model to automate web interactions.

### Tools:
- **[Browser Use](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/browser_use.py)** - Automates web browsing tasks using the browser-use agent, which employs Playwright and an LLM vision model to interact with websites

### API Keys required:
- LLM token (OpenAI or Google, depending on the chosen model)

---

## [People Researcher](https://github.com/supercog-ai/agentic/blob/main/examples/people_researcher.py)
This agent is designed to research people by searching for their LinkedIn profiles, selecting the correct profile with user input if needed, and generating detailed background reports on the person and their company.

### Tools:
- **LinkedIn Data Tool** - Provides functions to search LinkedIn profiles, retrieve profile information, and get company details using the RapidAPI LinkedIn Data API
- **Person Report Writer** - A sub-agent that generates detailed reports on a person based on their LinkedIn profile and company information
- **Company Reporter** - A sub-agent used by the Person Report Writer to research and report on companies

### API Keys required:
- LLM token (OpenAI)
- RapidAPI key (for LinkedIn Data API)

The People Researcher agent utilizes the LinkedIn Data Tool to search for and retrieve LinkedIn profile information. It interacts with users to select the correct profile when multiple matches are found. The agent then uses the Person Report Writer sub-agent to generate comprehensive background reports on the person and their company.

The agent supports different language models, with commented-out options for alternative models like LM Studio's Qwen and DeepSeek. It operates in a REPL loop, allowing for continuous interaction with users.

---

## [Podcast Long](https://github.com/supercog-ai/agentic/blob/main/examples/podcast/podcast_long.py)
This agent generates a combined podcast audio file by scraping news articles, summarizing their content, converting them to audio, and uploading the result to Transistor FM as a new episode. It uses multiple tools to accomplish this task, including web scraping, text-to-speech conversion, and API interactions.

### Tools:
- **[PodcastTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/podcast_tool.py)** - Scrapes news articles, summarizes content, and creates podcast audio files
- **[TextToSpeechTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/text_to_speech_tool.py)** - Converts text to speech using OPENAI
- **[AuthorizedRestApiTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/auth_rest_api_tool.py)** - Makes authenticated REST API calls to Transistor FM

### API Keys required:
- LLM token (OpenAI GPT-4)
- Transistor FM API key (TRANSISTOR_API_KEY)

---

## [Podcast Short](https://github.com/supercog-ai/agentic/blob/main/examples/podcast/podcast_short.py)
This agent automates the process of creating and publishing a daily news podcast. It generates content for AI, sports, and finance news segments, formats the content for broadcast, converts it to speech, and publishes the resulting audio file to Transistor.fm.

### Tools:
- **[Google News Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/google_news_tool.py)** - Retrieves news articles and headlines from Google News
- **[Tavily Search Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/tavily_search_tool.py)** - Performs web searches and retrieves information using the Tavily API
- **[Text To Speech Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/text_to_speech_tool.py)** - Converts text to speech using OpenAI's Text-to-Speech API

### API Keys required:
- LLM token (OpenAI for GPT-4O-MINI, Anthropic for CLAUDE)
- OpenAI API key (for Text-to-Speech)
- Transistor.fm API key (TRANSISTOR_API_KEY environment variable)
- Tavily API key (for web searches)

---

## [Rag Agent](https://github.com/supercog-ai/agentic/blob/main/examples/learning/rag_agent.py)
This agent utilizes a Retrieval-Augmented Generation (RAG) tool to answer questions based on a specific knowledge base, focusing on information from a predefined web page about AI tools helping teams move faster.

### Tools:
- **[RAG Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/rag_tool.py)** - Manages a knowledge index for storing and retrieving information. It is initialized with content from a specific URL and used to search for relevant information when answering questions.

### API Keys required:
- LLM token (OpenAI, Anthropic, etc.) for the underlying language model used by the Agent
- No additional API keys are explicitly required for the RAG Tool based on the provided code

---

## [Sequential Thinking Agent](https://github.com/supercog-ai/agentic/blob/main/examples/learning/sequential_thinking_agent.py)
This agent utilizes the Sequential Thinking MCP (Model Control Protocol) tool to break down complex problems into manageable steps. It provides a structured approach to problem-solving using sequential thinking techniques.

### Tools:
- **[MCPTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/mcp_tool.py)** - A universal wrapper for MCP tools that can work with any MCP server. In this case, it's used to initialize and interact with the Sequential Thinking MCP server.

### API Keys required:
- LLM token (OpenAI GPT-4)

The Sequential Thinking Agent is designed to assist users in breaking down complex problems into smaller, more manageable steps. It uses the MCPTool to interact with a Sequential Thinking MCP server, which provides the core functionality for structured problem-solving.

The agent is initialized with specific instructions on how to approach problems using sequential thinking, including breaking down problems, carefully considering each step, revising thinking when necessary, and exploring alternative approaches.

The agent uses the GPT-4 model from OpenAI for natural language processing and generation. It runs in a REPL (Read-Eval-Print Loop) environment, allowing for interactive problem-solving sessions with users.

Error handling is implemented for the initialization of the Sequential Thinking MCP tool, ensuring that the agent gracefully handles any setup issues.

---

## [Standup Agent](https://github.com/supercog-ai/agentic/blob/main/examples/standup_agent.py)
This agent prepares and assists with development standup meetings. It gathers information about open pull requests, including reviews and comments, and provides a summary of commits made in the last week using GitHub data.

### Tools:
- **[Github Tool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/github_tool.py)** - Interacts with the GitHub API to retrieve information about repositories, pull requests, and commits.

### API Keys required:
- LLM token (OpenAI API key for GPT-4O-MINI model)
- GitHub API key (for accessing repository data)

---

## [Testing](https://github.com/supercog-ai/agentic/blob/main/examples/learning/testing.py)
This agent is designed for unit testing purposes. It provides access to various testing functions through the UnitTestingTool and interacts with the user via a REPL loop. The agent uses GPT-4 to interpret instructions and execute testing functions.

### Tools:
- **[UnitTestingTool](https://github.com/supercog-ai/agentic/blob/main/src/agentic/tools/unit_test_tool.py)** - Provides various functions for testing scenarios including file operations, simulated delays, asynchronous function testing, and logging capabilities.

### API Keys required:
- LLM token (OpenAI)

---

## [Tool Builder](https://github.com/supercog-ai/agentic/blob/main/examples/tool_builder.py)
Tool Builder is an AI agent designed to assist users in creating new "AI agent" tools. It guides users through the process of defining, designing, and coding custom tools that can be used to extend the capabilities of AI agents.

### Tools:
This agent does not use any additional tools.

### API Keys required:
- LLM token (Anthropic API key for Claude)

The Tool Builder agent uses the Claude language model from Anthropic to generate responses and assist in tool creation. It doesn't utilize any additional tools beyond the core conversational capabilities provided by the language model.

The agent follows a structured approach to help users create new tools:
1. It asks the user about their desired tool functionality and seeks clarification on operational details.
2. It determines the authentication requirements for the tool, such as API keys or OAuth2 flow.
3. It explains the intended design for the tool based on the user's requirements.
4. It generates code for the tool, using an example tool definition as a reference.
5. It allows the user to request changes or modifications to the generated tool.

The agent is initialized with an example tool definition loaded from the `example_tool.py` file, which serves as a template for creating new tools.

---

## [Weather Agent](https://github.com/supercog-ai/agentic/blob/main/examples/learning/weather_agent.py)
This is a simple "hello world" agent example that provides basic weather information. The agent uses a simulated weather function to respond to weather-related queries.

### Tools:
- **weather_tool** - Returns a static string with simulated weather information

### API Keys required:
- LLM token (OpenAI)

---

