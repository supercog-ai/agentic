# LinkedinDataTool

The `LinkedinDataTool` provides access to LinkedIn profile and company data. This tool allows agents to retrieve information about professionals and organizations on LinkedIn through a third-party API.

## Features

- Retrieve detailed LinkedIn profile information
- Get company data by username or domain
- Search for LinkedIn profiles by various criteria
- Extract location IDs for more targeted searches

## Authentication

Requires a RapidAPI key with access to the LinkedIn Data API, which can be:

- Set in the environment as `RAPIDAPI_KEY`
- Retrieved through the tool's `get_api_key` method

## Methods

### get_linkedin_profile_info

```python
async def get_linkedin_profile_info(profile_url: str) -> str
```

Retrieves profile information for a LinkedIn user.

**Parameters:**

- `profile_url (str)`: Full LinkedIn profile URL (e.g., https://www.linkedin.com/in/username/)

**Returns:**
A string representation of the profile data as a pandas DataFrame.

### get_company_linkedin_info

```python
async def get_company_linkedin_info(company_username_or_domain: str) -> str | pd.DataFrame
```

Queries the LinkedIn Data API to get company information either by username or domain.

**Parameters:**

- `company_username_or_domain (str)`: Company username (e.g., "Google") or domain (e.g., "google.com")

**Returns:**
A pandas DataFrame containing company information or an error message.

### linkedin_people_search

```python
async def linkedin_people_search(name: Optional[str] = None, location: Optional[str] = None, job_title: Optional[str] = None, company: Optional[str] = None, start: str = "0") -> list[dict]
```

Searches for LinkedIn profiles based on various criteria.

**Parameters:**

- `name (Optional[str])`: Full name or partial name to search for
- `location (Optional[str])`: Either a location name (e.g., "California") or a geo ID (e.g., "102095887")
- `job_title (Optional[str])`: Job title to search for
- `company (Optional[str])`: Company name to search for
- `start (str)`: Start index for pagination (0, 10, 20, etc.)

**Returns:**
A list of dictionaries containing profile information.

### search_location

```python
async def search_location(keyword: str) -> str
```

Search for LinkedIn location ID by keyword.

**Parameters:**

- `keyword (str)`: Location name to search for (e.g., "California")

**Returns:**
Location ID for the first matching result.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools.linkedin_tool import LinkedinDataTool

# Set up the API key
# os.environ["RAPIDAPI_KEY"] = "your-rapidapi-key"

# Create an agent with LinkedIn data capabilities
linkedin_agent = Agent(
    name="LinkedIn Researcher",
    instructions="You help gather information about professionals and companies on LinkedIn.",
    tools=[LinkedinDataTool()]
)

# Use the agent to look up profile information
response = linkedin_agent << "Find information about Satya Nadella on LinkedIn"
print(response)

# Use the agent to research a company
response = linkedin_agent << "Get information about Microsoft from LinkedIn"
print(response)

# Use the agent to search for professionals
response = linkedin_agent << "Find data scientists working at Google in California"
print(response)
```

## Response Format

### Profile Information
The profile data is returned as a DataFrame with fields such as:

- Full name
- Headline
- Current and past positions
- Education
- Skills
- Location
- Connection count
- Profile URL and image URL

### Company Information
The company data is returned as a DataFrame with fields such as:

- Name
- Industry
- Location
- Website
- Description
- Employee count
- Founded date
- Specialties
- Logo URL

## Notes

- This tool requires a subscription to the "LinkedIn Data API" on RapidAPI
- Rate limits apply based on your RapidAPI subscription plan
- Results are cached to minimize API calls
- The tool provides asynchronous methods for better performance
- Location IDs can be used for more precise searches
- Search results are automatically converted to pandas DataFrames for easier processing
