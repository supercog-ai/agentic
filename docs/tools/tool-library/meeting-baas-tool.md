# MeetingBaasTool

The `MeetingBaasTool` provides capabilities for managing video meetings, recording transcripts, and generating summaries. This tool integrates with the MeetingBaaS API to join online meetings, record conversations, and process the resulting data.

## Features

- Join video meetings with a bot participant
- Record and transcribe meeting conversations
- Generate detailed meeting summaries
- Store and retrieve meeting information
- Answer questions about past meetings using RAG (Retrieval Augmented Generation)

## Authentication

Requires a MeetingBaaS API key, which can be stored in Agentic's secrets system as `MEETING_BAAS_API_KEY`.

## Methods

### join_meeting

```python
def join_meeting(meeting_url: str, thread_context: ThreadContext, bot_name: str = "Meeting Assistant") -> dict
```

Join a video meeting and start recording.

**Parameters:**

- `meeting_url (str)`: URL of the meeting to join
- `thread_context (ThreadContext)`: The execution context
- `bot_name (str)`: Name to display for the bot in the meeting (default: "Meeting Assistant")

**Returns:**
A dictionary with status information and meeting ID.

### get_transcript

```python
def get_transcript(meeting_id: str) -> dict
```

Get the transcript for a specific meeting and save it to the database if not already present.

**Parameters:**

- `meeting_id (str)`: The ID of the meeting

**Returns:**
A dictionary containing the meeting transcript or an error message.

### get_summary

```python
def get_summary(meeting_id: str) -> dict
```

Generate a detailed summary of the meeting.

**Parameters:**

- `meeting_id (str)`: The ID of the meeting

**Returns:**
A dictionary containing the generated summary or an error message.

### list_meetings

```python
def list_meetings() -> dict
```

List all recorded meetings.

**Returns:**
A dictionary containing a list of meetings with metadata.

### get_meeting_info

```python
def get_meeting_info(meeting_id: str) -> dict
```

Retrieve detailed information about a specific meeting.

**Parameters:**

- `meeting_id (str)`: The ID of the meeting

**Returns:**
A dictionary containing comprehensive meeting information.

### answer_question

```python
def answer_question(meeting_id: str, question: str) -> dict
```

Answer a question related to a specific meeting using RAG.

**Parameters:**

- `meeting_id (str)`: The ID of the meeting
- `question (str)`: The question to answer about the meeting

**Returns:**
A dictionary containing relevant context to answer the question.

### process_webhook

```python
def process_webhook(webhook_data: dict) -> dict
```

Process webhook data received from MeetingBaaS.

**Parameters:**

- `webhook_data (dict)`: The webhook data received from MeetingBaaS

**Returns:**
A dictionary containing the processing status and any updated meeting information.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools import MeetingBaasTool

# Create an agent with meeting capabilities
meeting_agent = Agent(
    name="Meeting Assistant",
    instructions="You help users join, record, and summarize video meetings.",
    tools=[MeetingBaasTool()]
)

# Use the agent to join a meeting
response = meeting_agent << "Join the Zoom meeting at https://zoom.us/j/123456789"
print(response)

# Use the agent to get a meeting transcript
response = meeting_agent << "Get the transcript from my last meeting"
print(response)

# Use the agent to summarize a meeting
response = meeting_agent << "Summarize what was discussed in the marketing meeting yesterday"
print(response)
```

## Database Storage

The tool automatically stores meeting information in a SQLite database:

- Meeting metadata (ID, URL, start/end time, status)
- Transcripts
- Generated summaries
- Attendees
- Recording URLs

## RAG Implementation

The tool uses Retrieval Augmented Generation for answering questions about meetings:

1. Meeting summaries are indexed in a vector database (Weaviate)
2. Embeddings are created using the BAAI/bge-small-en-v1.5 model
3. When a question is asked, relevant chunks of meeting content are retrieved
4. The context is returned for the agent to formulate an answer

## Webhook Support

The tool can receive and process webhooks from the MeetingBaaS service:

- Meeting status changes
- Completion notifications
- Error reports

## Notes

- Requires a public URL for webhook callbacks (uses devtunnel for local development)
- Transcription is performed by the MeetingBaaS service
- Summaries are generated using OpenAI's GPT-4o model
- Meeting bots can join Zoom, Microsoft Teams, Google Meet, and other platforms
- Vector storage enables semantic search across meeting content