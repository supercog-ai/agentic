# AuthorizedRestApiTool

The `AuthorizedRestApiTool` is a specialized version of `RestApiTool` that provides a simplified way to make authenticated REST API calls. This tool streamlines authentication handling, making it ideal for working with APIs that require consistent authentication across multiple requests.

## Features

- Simplified authentication setup
- Support for Bearer tokens, Basic auth, API keys in parameters, and custom headers
- All the capabilities of the base REST API tool
- Automatic secret retrieval from Agentic's secret store

## Initialization

```python
def __init__(token_type: str, token_var: str, token_name: str = "Bearer")
```

**Parameters:**

- `token_type (str)`: Authentication type, one of "bearer", "basic", "parameter", or "header"
- `token_var (str)`: The name of the secret variable that contains the token value
- `token_name (str)`: The name used with the token (varies by auth method)

## Authentication Types

The tool supports the following authentication methods:

1. **Bearer Token**:
   ```python
   AuthorizedRestApiTool("bearer", "API_KEY_SECRET_NAME")
   ```
   Adds an `Authorization: Bearer <token>` header.

2. **Basic Auth**:
   ```python
   AuthorizedRestApiTool("basic", "BASIC_AUTH_SECRET")
   ```
   For basic auth, the secret should be in the format `username:password`.

3. **Parameter Auth**:
   ```python
   AuthorizedRestApiTool("parameter", "API_KEY_SECRET", "api_key")
   ```
   Adds the token as a query parameter (e.g., `?api_key=value`).

4. **Header Auth**:
   ```python
   AuthorizedRestApiTool("header", "API_KEY_SECRET", "X-API-Key")
   ```
   Adds a custom header with the specified name (e.g., `X-API-Key: value`).

## Methods

### get_resource

```python
async def get_resource(url: str, params: dict = {}, thread_context: RunContext = None)
```

Performs an HTTP GET request with authentication.

**Parameters:**

- `url (str)`: The URL to request
- `params (dict)`: Query parameters
- `thread_context (RunContext)`: The execution context

**Returns:**
The parsed response based on content type.

### post_resource

```python
async def post_resource(url: str, content_type: str = "application/json", data: str = "{}", thread_context: RunContext = None)
```

Performs an HTTP POST request with authentication.

**Parameters:**

- `url (str)`: The URL to request
- `content_type (str)`: The content type (default: "application/json")
- `data (str)`: Request body
- `thread_context (RunContext)`: The execution context

**Returns:**
The parsed response based on content type.

### put_resource

```python
async def put_resource(url: str, data: str = "{}", thread_context: RunContext = None)
```

Performs an HTTP PUT request with authentication.

**Parameters:**

- `url (str)`: The URL to request
- `data (str)`: JSON request body
- `thread_context (RunContext)`: The execution context

**Returns:**
The parsed response based on content type.

### patch_resource

```python
async def patch_resource(url: str, data: str = "{}", thread_context: RunContext = None)
```

Performs an HTTP PATCH request with authentication.

**Parameters:**

- `url (str)`: The URL to request
- `data (str)`: JSON request body
- `thread_context (RunContext)`: The execution context

**Returns:**
The parsed response based on content type.

### delete_resource

```python
async def delete_resource(url: str, thread_context: RunContext = None)
```

Performs an HTTP DELETE request with authentication.

**Parameters:**

- `url (str)`: The URL to request
- `thread_context (RunContext)`: The execution context

**Returns:**
The parsed response based on content type.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools import AuthorizedRestApiTool

# Set up the secret first
# agentic secrets set GITHUB_TOKEN=your_token_here

# Create an agent with authenticated API capability
github_api = AuthorizedRestApiTool("bearer", "GITHUB_TOKEN")
api_agent = Agent(
    name="GitHub API Client",
    instructions="You can make authenticated API calls to GitHub.",
    tools=[github_api]
)

# Use the agent to get user information
response = api_agent << "Get my GitHub profile information from https://api.github.com/user"
print(response)

# Use the agent to list repositories
response = api_agent << "List my repositories from https://api.github.com/user/repos"
print(response)

# Using an API key in a parameter
weather_api = AuthorizedRestApiTool("parameter", "WEATHER_API_KEY", "apikey")
weather_agent = Agent(
    name="Weather API Client",
    instructions="You can get weather data using the Weather API.",
    tools=[weather_api]
)

# Use the agent to get weather data
response = weather_agent << "Get the current weather for London from https://api.weatherapi.com/v1/current.json"
print(response)
```

## Setting Up Secrets

Before using the tool, you need to set up your secrets:

```bash
# For GitHub API
agentic secrets set GITHUB_TOKEN=your_github_token

# For Weather API
agentic secrets set WEATHER_API_KEY=your_weather_api_key
```

## Common API Configurations

1. **GitHub API**:
   ```python
   AuthorizedRestApiTool("bearer", "GITHUB_TOKEN")
   ```

2. **OpenAI API**:
   ```python
   AuthorizedRestApiTool("bearer", "OPENAI_API_KEY")
   ```

3. **RapidAPI**:
   ```python
   AuthorizedRestApiTool("header", "RAPIDAPI_KEY", "X-RapidAPI-Key")
   ```

4. **AWS Signature v4**:
   ```python
   # For AWS, use a custom tool that implements Signature v4 auth
   # The AuthorizedRestApiTool is for simpler auth methods
   ```

## Notes

- The tool automatically retrieves the token value from the agent's secret store
- If the token is not found, the tool will raise an error
- The authentication is automatically applied to all requests
- For different APIs that require different authentications, create multiple instances of the tool
- The tool inherits all capabilities from RestApiTool
- For more complex authentication schemes like OAuth 2.0 flows, additional tools may be needed
