# RestApiTool

The `RestApiTool` is a powerful tool that enables agents to make HTTP requests to REST APIs. It supports various authentication methods, request types, and content formats, making it suitable for interacting with a wide range of web services.

This tool can be used in lieu of a specific tool for an external service. When developing an agent consider first using this tool, and as needs get more specific you can create a more specific tool.

## Features

- Multiple HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Various authentication methods (Bearer token, Basic auth, Parameter auth)
- JSON and form data request types
- Automatic response parsing based on content type
- Request header customization
- Configurable request parameters

## Methods

### prepare_auth_config

```python
async def prepare_auth_config(auth_type: str, username: str = None, password: str = None, token: str = None, token_name: str = "Bearer", thread_context: ThreadContext = None) -> AsyncGenerator[Any, Any]
```

Constructs an auth_config object to use with later requests.

**Parameters:**

- `auth_type (str)`: One of: "basic", "bearer", "token", "parameter", or "none"
- `username (str)`: Username for basic auth
- `password (str)`: Password for basic auth
- `token (str)`: Token for bearer or parameter auth
- `token_name (str)`: Name to use with the token (default: "Bearer")
- `thread_context (ThreadContext)`: The execution context

**Returns:**
The variable name of the auth config for use in request calls.

### add_request_header

```python
def add_request_header(auth_config_var: str, name: str, value: str) -> str
```

Add a header to the auth config which was created already.

**Parameters:**

- `auth_config_var (str)`: The auth config identifier
- `name (str)`: Header name
- `value (str)`: Header value

**Returns:**
"OK" on success.

### get_resource

```python
async def get_resource(url: str, params: dict = {}, auth_config_var: Optional[str] = "", thread_context: ThreadContext = None)
```

Invoke the GET REST endpoint on the indicated URL.

**Parameters:**

- `url (str)`: The URL to request
- `params (dict)`: Query parameters
- `auth_config_var (Optional[str])`: Auth config identifier
- `thread_context (ThreadContext)`: The execution context

**Returns:**
The parsed response based on content type.

### post_resource

```python
async def post_resource(path: str, content_type: str = "application/json", data: Union[str, dict] = "{}", auth_config_var: Optional[str] = "")
```

Invoke the POST REST endpoint.

**Parameters:**

- `path (str)`: The URL to request
- `content_type (str)`: The content type (default: "application/json")
- `data (str or dict)`: Request body
- `auth_config_var (Optional[str])`: Auth config identifier

**Returns:**
The parsed response based on content type.

### put_resource

```python
async def put_resource(url: str, data: str = "{}", auth_config_var: Optional[str] = "")
```

Invoke the PUT REST endpoint.

**Parameters:**

- `url (str)`: The URL to request
- `data (str)`: JSON request body
- `auth_config_var (Optional[str])`: Auth config identifier

**Returns:**
The parsed response based on content type.

### patch_resource

```python
async def patch_resource(url: str, data: str = "{}", auth_config_var: Optional[str] = "")
```

Invoke the PATCH REST endpoint.

**Parameters:**

- `url (str)`: The URL to request
- `data (str)`: JSON request body
- `auth_config_var (Optional[str])`: Auth config identifier

**Returns:**
The parsed response based on content type.

### delete_resource

```python
async def delete_resource(url: str, auth_config_var: Optional[str] = "")
```

Invoke the DELETE REST endpoint.

**Parameters:**

- `url (str)`: The URL to request
- `auth_config_var (Optional[str])`: Auth config identifier

**Returns:**
The parsed response based on content type.

### debug_request

```python
def debug_request(request_name: str)
```

Returns debug information about a request configuration.

**Parameters:**

- `request_name (str)`: The request configuration to debug

**Returns:**
A string with debug information.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools.rest_tool_v2 import RestApiTool

# Create an agent with REST API capabilities
api_agent = Agent(
    name="API Client",
    instructions="You help users interact with REST APIs.",
    tools=[RestApiTool()]
)

# Use the agent to make API calls
response = api_agent << """
First, set up authentication for the GitHub API:
1. Create a bearer token auth config
2. Then, get my user information from https://api.github.com/user
"""
print(response)

# Use the agent to make a POST request with data
response = api_agent << """
Create a new gist on GitHub:
1. Prepare bearer token auth
2. POST to https://api.github.com/gists with this data:
{
  "description": "Example Gist",
  "public": true,
  "files": {
    "example.txt": {
      "content": "Hello World"
    }
  }
}
"""
print(response)
```

## Response Handling

The tool automatically processes responses based on their Content-Type:

- JSON responses are parsed into Python dictionaries
- Images are converted to base64 and returned as data URLs
- HTML, plain text, and CSV are returned as strings
- Optionally, JSON responses can be converted to pandas DataFrames

## Authentication Types

1. **Basic Auth**:
   ```python
   # Called by the agent
   auth_var = await prepare_auth_config("basic", "username", "password")
   ```

2. **Bearer Token**:
   ```python
   # Called by the agent
   auth_var = await prepare_auth_config("bearer", token="your_token")
   ```

3. **Parameter Auth**:
   ```python
   # Called by the agent
   auth_var = await prepare_auth_config("parameter", token="your_api_key", token_name="api_key")
   ```

## Notes

- For authenticated requests, `prepare_auth_config` must be called first
- The tool supports both synchronous and asynchronous operations
- Error responses include both status code and response text
- Secret values can be retrieved from the ThreadContext
- The tool can be extended with custom response processors
- Variable substitution using `${ENV_VAR}` syntax is supported in auth parameters
