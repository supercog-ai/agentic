# IMAPTool

The `IMAPTool` provides email inbox access capabilities via the IMAP protocol. This tool allows agents to retrieve, list, and send emails, providing a comprehensive interface for email management.

## Features

- Connect to email accounts using IMAP
- List and retrieve emails with filtering options
- Send and draft emails
- Extract email content and attachments
- Process emails with tracking to avoid duplicates

## Authentication

Requires email credentials which can be:

- Stored in Agentic's secrets system as `IMAP_USERNAME` and `IMAP_PASSWORD`
- For Gmail, it's recommended to use an App Password rather than your account password

## Methods

### list_folders

```python
def list_folders(run_context: RunContext) -> List[str]
```

List all available folders in the email account.

**Parameters:**

- `run_context (RunContext)`: The execution context

**Returns:**
List of folder names.

### list_emails

```python
def list_emails(run_context: RunContext, limit: int = 50, subject_words: str = None, days_back_from_today: int = 1, direct_mail_only: bool = True, folder: str = "INBOX") -> List[Dict[str, Any]]
```

List emails in the inbox, optionally filtering by subject words.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `limit (int)`: Maximum number of emails to return
- `subject_words (str)`: Filter emails by these words in subject
- `days_back_from_today (int)`: Number of days back to retrieve
- `direct_mail_only (bool)`: If True, filter out newsletters and marketing emails
- `folder (str)`: Folder to search in (e.g., "INBOX", "Sent", "Drafts")

**Returns:**
List of dictionaries containing email information.

### send_email

```python
def send_email(run_context: RunContext, to: str, subject: str, body: str, save_draft: bool = True) -> str
```

Drafts or sends an email message.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `to (str)`: Recipient email address
- `subject (str)`: Email subject
- `body (str)`: Email body content
- `save_draft (bool)`: If True, save as draft; if False, send immediately

**Returns:**
Confirmation message.

### save_email_draft

```python
def save_email_draft(run_context: RunContext, to: str, subject: str, body: str) -> str
```

Save a draft email message.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `to (str)`: Recipient email address
- `subject (str)`: Email subject
- `body (str)`: Email body content

**Returns:**
Confirmation message.

### retrieve_emails

```python
def retrieve_emails(run_context: RunContext, limit: int = 5, search_criteria: str = "", since_date: Optional[str | datetime] = None, to_address: Optional[str] = None, subject_words: Optional[str] = None, folder: str = "INBOX") -> List[Dict[str, Any]]
```

Retrieve emails from the specified folder without tracking read status.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `limit (int)`: Maximum number of emails to retrieve
- `search_criteria (str)`: IMAP search string for filtering emails
- `since_date (Optional[str | datetime])`: Only retrieve emails after this date
- `to_address (Optional[str])`: Filter emails sent to this address
- `subject_words (Optional[str])`: Filter emails containing these words in subject
- `folder (str)`: Email folder to search in

**Returns:**
List of dictionaries containing email data.

### retrieve_emails_once

```python
def retrieve_emails_once(run_context: RunContext, limit: int = 5, search_criteria: str = "", since_date: Optional[str | datetime] = None, to_address: Optional[str] = None, subject_words: Optional[str] = None, folder: str = "INBOX") -> List[Dict[str, Any]]
```

Retrieve emails while tracking which emails have been read.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `limit (int)`: Maximum number of emails to retrieve
- `search_criteria (str)`: IMAP search string for filtering emails
- `since_date (Optional[str | datetime])`: Only retrieve emails after this date
- `to_address (Optional[str])`: Filter emails sent to this address
- `subject_words (Optional[str])`: Filter emails containing these words in subject
- `folder (str)`: Email folder to search in

**Returns:**
List of dictionaries containing email data (only unread/unprocessed emails).

## Example Usage

```python
from agentic.common import Agent
from agentic.tools import IMAPTool

# Create an agent with email capabilities
email_agent = Agent(
    name="Email Assistant",
    instructions="You help manage emails, retrieving and sending messages.",
    tools=[IMAPTool()]
)

# The agent will prompt for IMAP credentials if they aren't already set
# agentic set-secret IMAP_USERNAME "your.email@gmail.com"
# agentic set-secret IMAP_PASSWORD "your-app-password"

# Use the agent to check recent emails
response = email_agent << "Show me my latest emails"
print(response)

# Use the agent to search for specific emails
response = email_agent << "Find emails with 'invoice' in the subject from the last 7 days"
print(response)

# Use the agent to draft an email
response = email_agent << "Draft a response to the latest email from my boss"
print(response)
```

## Search Criteria Syntax

The tool supports IMAP search syntax for advanced filtering:

- `FROM "sender@example.com"`: Emails from a specific sender
- `SUBJECT "important"`: Emails with a specific subject word
- `TO "recipient@example.com"`: Emails to a specific recipient
- `SINCE "1-Jan-2023"`: Emails since a specific date
- `UNSEEN`: Unread emails
- `FLAGGED`: Starred/flagged emails

Criteria can be combined: `(FROM "amazon.com") AND (SUBJECT "order")`

## Notes

- The tool primarily supports Gmail but works with most IMAP-compatible email providers
- For Gmail, you need to enable "Less secure app access" or use an App Password
- Email attachments are saved to a temporary directory
- The tool tracks processed emails to avoid duplicates when using `retrieve_emails_once`
- HTML emails are automatically converted to plain text
