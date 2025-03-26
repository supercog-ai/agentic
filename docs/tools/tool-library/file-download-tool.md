# FileDownloadTool

The `FileDownloadTool` provides functionality for downloading files and content from URLs. This tool allows agents to retrieve files from the web and either save them locally or directly access their contents.

## Features

- Download files from URLs and save them locally
- Retrieve file contents without saving to disk
- Extract text content from HTML pages
- Handle redirects and various content types

## Methods

### download_url_as_file

```python
async def download_url_as_file(url: str, file_name_hint: str = "") -> str
```

Downloads a file from a URL and stores it locally.

**Parameters:**

- `url (str)`: The URL of the file to download
- `file_name_hint (str)`: Optional name for the saved file (default: extracted from URL)

**Returns:**
The file name of the saved file, or an error message if the download failed.

### download_file_content

```python
def download_file_content(url: str, limit: int = 4000) -> str
```

Downloads a file from the web and returns its contents directly.

**Parameters:**

- `url (str)`: The URL of the file to download
- `limit (int)`: Maximum number of characters to return (default: 4000)

**Returns:**
The content of the downloaded file, or an error message if the download failed.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools.file_download import FileDownloadTool

# Create an agent with file downloading capabilities
download_agent = Agent(
    name="File Downloader",
    instructions="You help users download files and extract content from web URLs.",
    tools=[FileDownloadTool()]
)

# Use the agent to download a file
response = download_agent << "Download the file from https://www.iana.org/reports/2014/transition-plan-201404.pdf"
print(response)

# Use the agent to get content directly
response = download_agent << "Get the content from https://www.iana.org/about"
print(response)
```

## Helper Methods

The tool provides these hidden helper methods:

- `get_last_path_component`: Extracts filename from URL path
- `_download_url_as_file`: Internal async method that handles the actual download

## Notes

- HTML content is automatically converted to plain text using html2text
- The tool follows redirects when downloading files
- File downloads are handled asynchronously
- For HTML content, a limit parameter controls how much text is returned
- If a filename isn't specified, it will be extracted from the URL
