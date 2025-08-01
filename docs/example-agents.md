# Example Agents

Agentic comes with several pre-built agents that demonstrate the framework's capabilities. All example agents can be found in the [`examples`](https://github.com/supercog-ai/agentic/tree/main/examples) folder of the GitHub repository.

## Basic Agent

The [Basic Agent](https://github.com/supercog-ai/agentic/blob/main/examples/basic_agent.py) is the simplest "hello world" example, demonstrating how to create an agent with access to tools. It uses the WeatherTool to answer questions about current weather conditions in various locations. This agent is ideal for beginners to understand the core concepts of the Agentic framework, showing how to:

- Define an agent with a name, welcome message, and instructions
- Attach tools to an agent
- Run an agent in interactive mode

The Basic Agent serves as an excellent starting point for anyone new to the framework, requiring minimal setup while demonstrating the fundamental agent-tool interaction pattern.

## OSS Deep Researcher

The [OSS Deep Researcher](https://github.com/supercog-ai/agentic/tree/main/examples/deep_research) performs comprehensive web research on any topic and writes a detailed, multiple-page report based on its findings. This complex agent exemplifies a "plan and execute" approach, orchestrating a team of specialized sub-agents across multiple steps:

1. Gathers the research topic from the user and generates initial web search queries
2. Uses the search results to create a structured report plan with sections
3. For each section, generates targeted search queries to gather specific information
4. Drafts each section based on the research findings
5. Reviews and refines each section with context from the entire report
6. Generates comprehensive source references

The Deep Researcher showcases advanced agent orchestration techniques, web research capabilities, and document generation. It's an excellent example of how complex workflows can be managed through the Agentic framework, making it ideal for educational, research, or content creation applications.

## OSS Operator

The [OSS Operator](https://github.com/supercog-ai/agentic/blob/main/examples/oss_operator.py) agent provides intelligent, LLM-directed browser automation. This agent can fully interact with any website, filling forms, clicking buttons, navigating pages, and extracting information based on natural language instructions. It uses the BrowserUseTool which leverages Playwright for browser automation.

Key capabilities include:

- Full web interaction through natural language commands
- Visual reasoning to understand web page elements
- Screenshot capture and analysis
- Form filling and submission
- Navigation across multiple pages
- Session persistence (optional)

The OSS Operator can be configured to use your actual Chrome browser instance, including your cookies and local storage, making it powerful for automating tasks that require authenticated sessions. This agent is particularly useful for web scraping, data collection, form automation, and testing web applications.

## Meeting Notetaker

The [Meeting Notetaker](https://github.com/supercog-ai/agentic/blob/main/examples/meeting_notetaker.py) agent can join online meetings to record, transcribe, and summarize them. It creates comprehensive meeting summaries that can be reviewed later and stores both summaries and transcripts in a RAG (vector store) index for future reference.

Key features include:

- Joining meetings through provided URLs
- Real-time recording and transcription
- Generating structured meeting summaries
- Building a searchable knowledge base of past meetings
- Answering questions about meeting content using RAG

This agent demonstrates how Agentic can be used for practical workplace applications, combining real-time processing with knowledge management. It's particularly useful for teams looking to maintain institutional knowledge and improve meeting documentation.

## Podcast Producer

The [Podcast Producer](https://github.com/supercog-ai/agentic/blob/main/examples/podcast) agent automatically creates and publishes daily podcasts. The agent handles the complete workflow from content generation to audio production and publication. It showcases how to:
- Use text-to-speech tools for audio content generation
- Integrate with third-party APIs (Transistor.fm)
- Handle multi-stage content workflows


### Short Podcast Agent

The [Short Podcast Agent](https://github.com/supercog-ai/agentic/blob/main/examples/podcast/podcast_short.py) demonstrates the use of agent teams and pipelines in Agentic.

Key features:

- Multi-agent team with AI, sports, and finance reporters
- Compiles short daily summary using a producer agent
- Publishes audio via Transistor.fm API

This example is particularly valuable for understanding how to coordinate multiple agents to accomplish complex tasks that involve content creation, transformation, and distribution.

### Long Podcast Agent

The [Long Podcast Agent](https://github.com/supercog-ai/agentic/blob/main/examples/podcast/podcast_long.py) creates longer, more in-depth podcasts.

Key features:

- Scrapes and downloads news articles
- Summarizes articles and converts to audio
- Stitches segments and publishes via Transistor.fm API

Steps to set up ngrok devtunnel (to host audio url):

1. [Download ngrok](https://ngrok.com/downloads/mac-os)
2. Login, retrieve auth token and run `ngrok config add-authtoken <your_auth_token>`
3. Start local server by running `python -m http.server 8000`
4. In a separate terminal, run `ngrok http 8000`
5. Use the output url as the `base_url` (e.g. `https://<your-ngrok-id>.ngrok-free.app`)

This example demonstrates how to produce long-form content using external tools and APIs for content gathering, transformation, and distribution.

## Database Agent

The [Database Agent](https://github.com/supercog-ai/agentic/blob/main/examples/database/database_agent.py) demonstrates basic Text-to-SQL capabilities for performing data analysis using natural language. This agent connects to a database and allows users to:

- Query database structure and schema
- Ask questions about the data in plain English
- Get results from complex SQL queries without writing any SQL
- Explore data relationships and patterns

The Database Agent shows how Agentic can be used for data analysis tasks, making databases accessible through natural language. It's an excellent example of how the framework can bridge complex technical systems with intuitive interfaces, allowing non-technical users to interact with databases without SQL knowledge.



## GitHub Agent

The [GitHub Agent](https://github.com/supercog-ai/agentic/blob/main/examples/github.py) enables interaction with GitHub repositories through natural language. This agent leverages the GitHub API to:

- Search repositories for specific code or content
- Create, view, and manage issues
- Generate pull requests
- Access repository statistics and information
- Browse file structures and content

The agent maintains context about recently viewed repositories and has built-in memory to improve interactions. This example demonstrates how to create tools that integrate with external APIs and services, while providing a natural language interface to complex systems.

## Study Guide Agent
The [Study Guide Agent](https://github.com/supercog-ai/agentic/blob/main/examples/study/study_guide.py) demonstrates using the RAG tool to provide an agent with additional context. The agent helps the user study content using knowledge from a RAG index. It has 3 main features:

- Test Prep: The agent creates a set of short answer questions and evaluates the user's answers
- Study Buddy: The agent converses with the user about the source document and suggests further readings
- Multiple Choice Quiz: The agent generates a multiple choice quiz and an answer key using content in the documents.

The Study Guide Agent shows the strength of using RAG in agent deployment, using specific knowledge from provided documents instead of inaccurate, general knowledge. It demonstrates how Agentic can be used to create agents specific to a user's data and knowledge.

## Next Steps

- Learn more about the [Tools](./tools//tool-library/index.md) that power these agents - each tool has a basic demo agent you can run
- Check out [RAG Support](./rag-support.md) to give your agents access to your own knowledge base
- Build your own Agents! Think about some of these ideas, or come up with your own:
    - Build a "conversational assistant" agent that can answer questions from private documents,
    or by retrieving information live from systems like JIRA or Salesforce.

    - Build a customer service agent that answers questions from a RAG index plus live data sources 
    (status of orders, status of tickets, etc...).

    - Adapt the Deep Research agent to do research projects _inside your company_. Either connect
    live data sources via search APIs (like Google Docs search, or Salesforce SOQL), or build a 
    RAG index that contains docs and knowledge from your company.

    - Create an agent that uses browser automation to gather information from a site that requires
    user login, and store that information in a structured form like a spreadsheet.

    - Create an agent that does people+company research from a list of leads in a spreadsheet,
    writing the research data back into the spreadsheet.

