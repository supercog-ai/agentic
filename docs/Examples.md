# Example agents

All example agents can be found in the `examples` folder.

## Deep Researcher

The OSS Deep Researcher performs web research on any topic, and writes a multiple page
report based on its research findings. This complex agent is an example of a "plan and execute"
agent which operates across many steps.

## Operator

Our version of the OpenAI "Operator" agent supports intelligent LLM-directed browser automation.
You can fully automate live interaction with any web site. This agent relies on a browser
automation tool which you can use for your own agents.

## Meeting Notetaker

The Meeting Notetaker agent can dispatch a "meeting bot" to transcribe notes from your online
meetings. It creates a summary of each meeting which you can review later, and stores the
summaries and transcripts in a RAG (vector store) index so you can ask questions about
meetings long after they have ended.

## People Researcher

The People Researcher agent uses a LinkedAPI scraper API to do research via LinkedIn 
on contacts that you specify.

## AirBnb calendar agent

The AirBnb agent can help AirBnb hosts manage their bookings calendar.

## Database Agent

The Database Agent demonstrates basic Text-to-SQL for performing data analysis using
natural language.
 
## Agentic Oracle

This basic Q&A chatbot builds a RAG index from the Agentic library docs, and it can
answer questions using Retrievel Augmented Generation based on that imdex.

# What else can I build?

Here are some other ideas for useful agents:

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

