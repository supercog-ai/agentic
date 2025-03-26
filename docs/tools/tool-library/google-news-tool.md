# GoogleNewsTool

The `GoogleNewsTool` provides access to Google News articles and headlines through a variety of search and filtering methods. This tool allows your agents to retrieve current news, topic-specific news, perform advanced searches, and analyze trending topics.

## Features

- Get top headlines from Google News
- Search for news by topic, keyword, or location
- Advanced search options (exact phrases, exclusions, site-specific searches)
- Download and extract full article content
- Analyze trending and local topics

## Methods

### get_top_headlines

```python
def get_top_headlines(language: str = "en", country: str = "US") -> pd.DataFrame
```

Retrieves the current top headlines from Google News.

**Parameters:**

- `language (str)`: The language code (default: "en")
- `country (str)`: The country code (default: "US")

**Returns:**
A pandas DataFrame containing the top headlines.

### query_topic

```python
def query_topic(topic: str, language: str = "en", country: str = "US") -> pd.DataFrame
```

Retrieves news articles related to a specific topic.

**Parameters:**

- `topic (str)`: The topic to search for
- `language (str)`: The language code (default: "en")
- `country (str)`: The country code (default: "US")

**Returns:**
A pandas DataFrame containing news articles related to the topic.

### query_news

```python
def query_news(query: str, language: str = "en", country: str = "US", before: date = None, after: date = None, back_days: int = 1, exact_phrase: str = None, exclude_terms: List[str] = None, site: str = None, in_title: bool = False, in_url: bool = False, all_in_text: bool = False) -> pd.DataFrame
```

Performs an advanced search for news articles with multiple filtering options.

**Parameters:**

- `query (str)`: The main search query
- `language (str)`: The language code (default: "en")
- `country (str)`: The country code (default: "US")
- `before (Optional[date])`: End date for articles
- `after (Optional[date])`: Start date for articles
- `back_days (int)`: Number of days back to search (default: 1)
- `exact_phrase (Optional[str])`: Phrase that must appear exactly as written
- `exclude_terms (Optional[List[str]])`: Terms to exclude from results
- `site (Optional[str])`: Limit search to a specific news source
- `in_title (bool)`: Search only in article titles (default: False)
- `in_url (bool)`: Search only in article URLs (default: False)
- `all_in_text (bool)`: Require all words in the article text (default: False)

**Returns:**
A pandas DataFrame containing the search results.

### get_category_news

```python
def get_category_news(category: str, language: str = "en", country: str = "US") -> List[NewsItem]
```

Retrieves news from a specific category.

**Parameters:**

- `category (str)`: One of 'WORLD', 'NATION', 'BUSINESS', 'TECHNOLOGY', 'ENTERTAINMENT', 'SCIENCE', 'SPORTS', 'HEALTH'
- `language (str)`: The language code (default: "en")
- `country (str)`: The country code (default: "US")

**Returns:**
A pandas DataFrame containing news articles in the specified category.

### get_location_news

```python
def get_location_news(location: str, language: str = "en", country: str = "US", max_results: int = 10) -> List[NewsItem]
```

Retrieves news related to a specific location.

**Parameters:**

- `location (str)`: The location to get news for (e.g., "New York", "Tokyo")
- `language (str)`: The language code (default: "en")
- `country (str)`: The country code (default: "US")
- `max_results (int)`: Maximum number of results (default: 10)

**Returns:**
A pandas DataFrame containing location-specific news.

### get_local_topics

```python
def get_local_topics(location: str, language: str = "en", country: str = "US", num_topics: int = 10) -> Dict[str, Any]
```

Analyzes news to extract trending topics for a specific location.

**Parameters:**

- `location (str)`: The location to analyze (e.g., "New York", "Tokyo")
- `language (str)`: The language code (default: "en")
- `country (str)`: The country code (default: "US")
- `num_topics (int)`: Number of topics to return (default: 10)

**Returns:**
A dictionary containing trending local topics, their frequencies, and sample headlines.

### get_trending_topics

```python
def get_trending_topics(language: str = "en", country: str = "US", num_topics: int = 10) -> List[str]
```

Retrieves the currently trending topics on Google News.

**Parameters:**

- `language (str)`: The language code (default: "en")
- `country (str)`: The country code (default: "US")
- `num_topics (int)`: Number of topics to return (default: 10)

**Returns:**
A list of trending topics.

### explain_search_syntax

```python
def explain_search_syntax() -> str
```

Provides an explanation of the advanced search syntax for Google News.

**Returns:**
A string explaining the search syntax options.

### download_news_article

```python
async def download_news_article(title: str, url: str) -> str
```

Downloads and extracts the content of a news article.

**Parameters:**

- `title (str)`: The article title
- `url (str)`: The article URL

**Returns:**
The text content of the article.

## Example Usage

```python
from agentic.common import Agent
from agentic.tools.google_news import GoogleNewsTool

# Create a news agent
news_agent = Agent(
    name="News Reporter",
    instructions="You find and summarize news articles on requested topics.",
    tools=[GoogleNewsTool()]
)

# Use the agent
response = news_agent << "What are the top headlines today?"
print(response)

# Advanced search
response = news_agent << "Find news about climate initiatives from the past week"
print(response)
```
