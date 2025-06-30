# 📰 Project Design Document: Mini News Producer

## 📌 Overview

**Mini News Producer** is an autonomous AI agent built using the Agentic framework. It generates a daily news summary webpage by:
- Fetching top news articles via web search tools
- Summarizing them using an LLM
- Formatting the result into clean HTML
- Automatically saving and optionally opening the output in a web browser

---

## 🎯 Goals

- Generate a concise daily news summary from a diverse set of recent topics
- Ensure stories are from reliable sources and within the past 24 hours
- Format the output in a reader-friendly, web-based style with links and visuals
- Enable future extensibility for features like location-aware content, topic filtering, or scheduling

---

## 🛠️ Architecture

### Core Components

1. **News Collection System**
   - Uses Google News API and web search tools
   - Enforces time filter (24 hours)
   - Maintains topic diversity across 8 categories
   - Verifies source credibility

2. **Content Processing Pipeline**
   - AI-based headline generation
   - Two-paragraph summary creation
   - Image generation per article
   - Source link verification

3. **Presentation Layer**
   - Modern HTML/CSS design
   - Responsive card layout
   - HTML generation vs. CSS already given to maintain consistency

4. **HTML File Creation**
    - Creates a HTML file in the current directory
    - Opens the HTML file in the default web browser
    - Adapts to current system (Linux, MacOS)

---

## 📋 Technical Specifications

### Agents

1. **Headline News Reporter**
   - Role: News aggregation and summarization
   - Tools: Google News Tool, Web Search Tool
   - Model: GPT-4
   - Responsibilities:
     - Article selection
     - Headline generation
     - Summary creation
     - Source verification

2. **News Formatter**
   - Role: HTML generation and formatting
   - Tools: Image Generator
   - Model: GPT-4
   - Responsibilities:
     - HTML formatting
     - Image generation
     - Bullet point creation
     - Link formatting

---

## 🎯 Future Enhancements

### Planned Features

1. **Daily Update**
   - Create a system to automatically generate a new news summary every day
   - Send some kind of email or notification to the user with access to the news summary

2. **User Filtering**
    - Prompt user to select topics of interest
    - Allow user to select sources of interest
    - Filter articles based on user selection

3. **Location Awareness**
    - Location tool to give agent location of user
    - Filter articles based on location
    
### Fixes and updates

1. **Article Generation**
   - Issues with Google News API and OpenAI web search tool
   - Articles truncated and abreviated leading to hallucinations
   - 100 articles for each topic, over generation
   - Bogus links leading to 404s and irrelevent articles

2. **Image generation**
   - Images are generated big than cut down leading to loss of content
   - Poor image generation, often unrelated to article and not of high quality

3. **Article Selection**
   - Lack or recency, articles often very outdated despite specific time filter
   - Articles are not diverse enough, often same topic repeated
   - The articles are commenly not of high relevence or importance, only highest priority articles should be selected
   - Lack of source reliability and frequent halucinations

4. **Windows Compatibility**
   - Make file/webpage openable on windows

5. **REPL loop**
   - Move away from repl loop and remove dependency on user input

## 📝 Version

### Current Version
v1.0 - Basic implementation

### Change Log
- [v1.0] Initial release
  - Basic news aggregation
  - HTML generation
  - Simple styling

---

*Last Updated: June 30, 2025*
