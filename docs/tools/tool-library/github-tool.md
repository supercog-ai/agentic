# GithubTool

The `GithubTool` provides comprehensive access to GitHub operations and data. This tool allows agents to interact with GitHub repositories, issues, pull requests, and more through the GitHub API.

## Features

- Repository management (create, delete, clone, etc.)
- Issue and pull request management
- Code search and repository content browsing
- User information retrieval
- Git operations (commit, push, pull, branch management)

## Authentication

Requires a GitHub API key (personal access token) which can be:

- Passed during initialization as `api_key`
- Set in environment variables
- Stored in Agentic's secrets system as `GITHUB_API_KEY`

## Initialization

```python
def __init__(api_key: str = None, default_repo: str = None)
```

**Parameters:**

- `api_key (str)`: GitHub API token (optional if set in environment or secrets)
- `default_repo (str)`: Default repository to use in format "owner/repo"

## Remote API Methods

### search_repositories

```python
async def search_repositories(run_context: RunContext, query: str, language: Optional[str] = None, sort: str = 'stars', order: str = 'desc') -> dict
```

Search for GitHub repositories.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `query (str)`: Search keywords
- `language (Optional[str])`: Filter repositories by programming language
- `sort (str)`: Criteria to sort results ('stars', 'forks', 'updated')
- `order (str)`: Order of results ('asc', 'desc')

**Returns:**
A dictionary containing search results.

### create_github_issue

```python
async def create_github_issue(run_context: RunContext, title: str, body: str, labels: List[str] = None, repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> Dict[str, Any]
```

Create a new issue in a GitHub repository.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `title (str)`: Title of the issue
- `body (str)`: Body text of the issue
- `labels (List[str])`: Labels to apply to the issue
- `repo_owner (Optional[str])`: Repository owner (defaults to default_repo owner)
- `repo_name (Optional[str])`: Repository name (defaults to default_repo name)

**Returns:**
The created issue data or an error message.

### get_github_issues

```python
async def get_github_issues(run_context: RunContext, state: str = 'open', labels: Optional[str] = None, assignee: Optional[str] = None, creator: Optional[str] = None, mentioned: Optional[str] = None, since: Optional[str] = None, repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> pd.DataFrame
```

List issues in a repository.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `state (str)`: State of issues to return ('open', 'closed', 'all')
- `labels (Optional[str])`: Comma-separated list of label names
- `assignee (Optional[str])`: Username of assigned user
- `creator (Optional[str])`: Username of issue creator
- `mentioned (Optional[str])`: Username mentioned in issues
- `since (Optional[str])`: ISO 8601 timestamp for issues updated after this date
- `repo_owner (Optional[str])`: Repository owner
- `repo_name (Optional[str])`: Repository name

**Returns:**
A pandas DataFrame containing issue data.

### create_pull_request

```python
async def create_pull_request(run_context: RunContext, title: str, body: str, head: str, base: str, repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> Dict[str, Any]
```

Create a new pull request.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `title (str)`: Title of the pull request
- `body (str)`: Body of the pull request
- `head (str)`: The branch with changes
- `base (str)`: The branch to merge changes into
- `repo_owner (Optional[str])`: Repository owner
- `repo_name (Optional[str])`: Repository name

**Returns:**
Created pull request data.

### get_repository_contents

```python
async def get_repository_contents(run_context: RunContext, path: str = '', repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> List[Dict[str, Any]]
```

Get contents of a repository.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `path (str)`: Path to the content
- `repo_owner (Optional[str])`: Repository owner
- `repo_name (Optional[str])`: Repository name

**Returns:**
List of repository contents.

### search_in_repo

```python
async def search_in_repo(run_context: RunContext, query: str, repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> List[Dict[str, str]]
```

Search for code within a specific repository.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `query (str)`: Search terms or code snippet to find
- `repo_owner (Optional[str])`: Repository owner
- `repo_name (Optional[str])`: Repository name

**Returns:**
List of dictionaries with file paths, URLs, and code snippets.

### download_repo_file

```python
async def download_repo_file(run_context: RunContext, file_path: str, repo_owner: Optional[str] = None, repo_name: Optional[str] = None, branch: Optional[str] = None, local_file_name: Optional[str] = None) -> str
```

Download a file from a repository to local storage.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `file_path (str)`: Path to the file in the repository
- `repo_owner (Optional[str])`: Repository owner
- `repo_name (Optional[str])`: Repository name
- `branch (Optional[str])`: Branch to download from
- `local_file_name (Optional[str])`: Local filename to save as

**Returns:**
Local filename of the downloaded file or an error message.

## Local Git Operations

### clone_repository

```python
def clone_repository(run_context: RunContext, repo_url: str, directory_path: str) -> str
```

Clone a git repository from the given URL.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `repo_url (str)`: URL of the repository to clone
- `directory_path (str)`: Path where the repository should be cloned

**Returns:**
Status message.

### create_commit

```python
def create_commit(run_context: RunContext, repo_path: str, message: str, files: Optional[List[str]] = None) -> str
```

Create a commit in the local repository.

**Parameters:**

- `run_context (RunContext)`: The execution context
- `repo_path (str)`: Path to the local repository
- `message (str)`: Commit message
- `files (Optional[List[str]])`: List of file paths to commit

**Returns:**
Status message.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools import GithubTool

# Create a GitHub tool with authentication
github_tool = GithubTool(api_key="<YOUR-API-KEY>" default_repo="supercog-ai/agentic")

# Create an agent with GitHub capabilities
github_agent = Agent(
    name="GitHub Assistant",
    instructions="You help users interact with GitHub repositories.",
    tools=[github_tool]
)

# Use the agent to search repositories
response = github_agent << "Find the top 5 Python repositories for machine learning"
print(response)

# Use the agent for repository operations
response = github_agent << "Create an issue in the default repository with title 'Update documentation' and body 'The installation docs need updating.'"
print(response)
```

## Notes

- Most methods support either direct repository specification or using the default repository
- The tool handles authentication automatically once API key is provided
- For extensive git operations, local clones are created in a managed directory
- All API requests use asynchronous HTTP calls for better performance
- The tool provides both high-level GitHub API operations and low-level git operations
