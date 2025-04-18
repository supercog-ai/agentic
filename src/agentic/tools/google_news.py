from typing import Any, Callable, List, Dict
from collections import Counter
from datetime import date

import pandas as pd
from googlenewsdecoder import new_decoderv1
from google_news_feed import GoogleNewsFeed, NewsItem

from agentic.tools.scaleserp_browser import ScaleSerpBrowserTool
from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry, Dependency

@tool_registry.register(
    name="GoogleNewsTool",
    description="Functions for accessing Google News.",
    dependencies=[
        Dependency(
            name="google-news-feed",
            version="1.1.0",
            type="pip",
        ),
        Dependency(
            name="googlenewsdecoder",
            version="0.1.7",
            type="pip",
        ),
    ],
    config_requirements=[],
)

class GoogleNewsTool(BaseAgenticTool):
    """Functions for accessing Google News."""

    browser_tool: ScaleSerpBrowserTool = None

    def __init__(self):
        self.browser_tool = ScaleSerpBrowserTool()

    def get_tools(self) -> list[Callable]:
        return [
            self.get_top_headlines,
            self.query_topic,
            self.query_news,
            self.get_category_news,
            self.get_location_news,
            self.get_local_topics,
            self.get_trending_topics,
            self.explain_search_syntax,
            self.download_news_article,
        ]

    def _news_items_to_df(self, news_items: List[NewsItem]) -> dict:
        df = pd.DataFrame([item.__dict__ for item in news_items])
        # df['pubDate'] = pd.to_datetime(df['pubDate'], utc=True)
        # df['pubDate'] = df['pubDate'].dt.date
        return df

    def get_top_headlines(
        self, language: str = "en", country: str = "US"
    ) -> pd.DataFrame:
        """Gets top headlines for the specified language and country."""
        gnf = GoogleNewsFeed(language=language, country=country)
        results = gnf.top_headlines()
        return self._news_items_to_df(results)

    def query_topic(
        self, topic: str, language: str = "en", country: str = "US"
    ) -> pd.DataFrame:
        """Gets new articles related to the specified topic."""
        gnf = GoogleNewsFeed(language=language, country=country)
        results = gnf.query_topic(topic)
        return self._news_items_to_df(results)

    def query_news(
        self,
        query: str,
        language: str = "en",
        country: str = "US",
        before: date = None,
        after: date = None,
        back_days: int = 1,
        exact_phrase: str = None,
        exclude_terms: List[str] = None,
        site: str = None,
        in_title: bool = False,
        in_url: bool = False,
        all_in_text: bool = False,
    ) -> pd.DataFrame:
        """
        Searches for news articles based on the given query and parameters.

        Args:
            query (str): The main search query.
            language (str): The language for the search results.
            country (str): The country for the search results.
            before (Optional[date]): End date format YYYY-MM-DD.
            after (Optional[date]): Start date format YYYY-MM-DD.
            back_days: Number of days back to retrieve news
            exact_phrase (Optional[str]): Phrase that must appear exactly as written.
            exclude_terms (Optional[List[str]]): Terms to exclude from the search.
            site (Optional[str]): Limit search to a specific news source.
            in_title (bool): If True, search only in the title.
            in_url (bool): If True, search only in the URL.
            all_in_text (bool): If True, all words must appear in the body text.

        Returns:
            A DataFrame where each row is a news item.
        """
        gnf = GoogleNewsFeed(
            language=language, country=country, resolve_internal_links=False
        )

        # Construct advanced query
        if exact_phrase:
            query += f' "{exact_phrase}"'
        if exclude_terms:
            query += " " + " ".join([f'-"{term}"' for term in exclude_terms])
        if site:
            query += f" site:{site}"
        if in_title:
            query = f"intitle:{query}"
        if in_url:
            query = f"inurl:{query}"
        if all_in_text:
            query = f"allintext:{query}"

        results = gnf.query(query, before=before, after=after, when=f"{back_days}d")
        return self._news_items_to_df(results)

    def get_category_news(
        self, category: str, language: str = "en", country: str = "US"
    ) -> List[NewsItem]:
        """
        Gets news from a specific category.
        Categories: 'WORLD', 'NATION', 'BUSINESS', 'TECHNOLOGY', 'ENTERTAINMENT', 'SCIENCE', 'SPORTS', 'HEALTH'
        """
        gnf = GoogleNewsFeed(language=language, country=country)
        results = gnf.query_topic(category)
        return self._news_items_to_df(results)

    def get_location_news(
        self,
        location: str,
        language: str = "en",
        country: str = "US",
        max_results: int = 10,
    ) -> List[NewsItem]:
        """
        Gets news articles related to a specific location.

        Args:
            location (str): The specific location for which to retrieve news (e.g., "New York", "Paris", "Tokyo").
            language (str): The language for the news feed.
            country (str): The country for the news feed.
            max_results (int): The maximum number of articles to return.

        Returns:
            List[NewsItem]: A list of news articles related to the specified location.
        """
        gnf = GoogleNewsFeed(language=language, country=country)
        results = gnf.query(f'location:"{location}"')
        return self._news_items_to_df(results[:max_results])

    def get_local_topics(
        self,
        location: str,
        language: str = "en",
        country: str = "US",
        num_topics: int = 10,
    ) -> Dict[str, Any]:
        """
        Analyzes news to extract trending topics for a specific location.

        Args:
            location (str): The specific location for which to analyze news (e.g., "New York", "Paris", "Tokyo").
            language (str): The language for the news feed.
            country (str): The country for the news feed.
            num_topics (int): The number of local topics to return.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - 'topics': List of trending local topics
                - 'topic_frequencies': Dictionary of topic frequencies
                - 'sample_headlines': List of sample headlines for the top topics
        """
        gnf = GoogleNewsFeed(language=language, country=country)
        local_news = gnf.query(f'location:"{location}"')

        # Extract words from headlines
        words = []
        headlines = []
        for article in local_news:
            headline = article.title.lower()
            headlines.append(headline)
            words.extend(headline.split())

        # Remove common words and location name
        stop_words = set(
            [
                "the",
                "best",
                "a",
                "an",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "and",
                "or",
                "but",
                "is",
                "are",
                "was",
                "were",
            ]
        )
        stop_words.update(location.lower().split())
        words = [word for word in words if word not in stop_words and len(word) > 2]

        # Count word frequency and get top N most common words as local topics
        word_counts = Counter(words)
        local_topics = [word for word, _ in word_counts.most_common(num_topics)]

        # Get sample headlines for top topics
        sample_headlines = []
        for topic in local_topics[:5]:  # Get samples for top 5 topics
            for headline in headlines:
                if topic in headline and headline not in sample_headlines:
                    sample_headlines.append(headline)
                    break

        return {
            "topics": local_topics,
            "topic_frequencies": {
                topic: count for topic, count in word_counts.most_common(num_topics)
            },
            "sample_headlines": sample_headlines,
        }

    def get_trending_topics(
        self, language: str = "en", country: str = "US", num_topics: int = 10
    ) -> List[str]:
        """
        Retrieves a list of currently trending topics on Google News.

        This function approximates trending topics by analyzing the frequency of words
        in the top headlines. It's not an official "trending topics" feature, but it
        gives an indication of frequently mentioned topics.

        Args:
            language (str): The language for the news feed.
            country (str): The country for the news feed.
            num_topics (int): The number of trending topics to return.

        Returns:
            List[str]: A list of trending topics.
        """
        gnf = GoogleNewsFeed(language=language, country=country)
        headlines = gnf.top_headlines()

        # Extract words from headlines
        words = " ".join([article.title for article in headlines]).lower().split()

        # Remove common words (you might want to expand this list)
        stop_words = set(
            [
                "the",
                "a",
                "an",
                "best",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "and",
                "or",
                "but",
            ]
        )
        words = [word for word in words if word not in stop_words and len(word) > 2]

        # Count word frequency and get top N most common words as trending topics
        word_counts = Counter(words)
        trending_topics = [word for word, _ in word_counts.most_common(num_topics)]

        return trending_topics

    def explain_search_syntax(self) -> str:
        """Provides an explanation of the advanced search syntax."""
        explanation = """
        Google News RSS Advanced Search Syntax:

        1. Boolean OR Search: Use 'OR' between terms. E.g., 'SpaceX OR Boeing'
        2. Exact Match: Use quotes for exact phrases. E.g., "Elon Musk"
        3. Exclude Terms: Use '-' before terms to exclude. E.g., Apple -fruit
        4. Include Terms: Use '+' before terms that must be included. E.g., +Tesla earnings
        5. Site-specific: Use 'site:' to search within a specific news source. E.g., site:bbc.com
        6. Location: Use 'location:' to search for news about a specific place. E.g., location:"New York"
        7. Time Range: Use 'after:' and 'before:' for date range, or 'when:' for recent news.
           E.g., after:2023-01-01 before:2023-12-31 or when:1h, when:7d, when:1m
        8. In Title: Use 'intitle:' to search in the title only. E.g., intitle:Tesla
        9. In URL: Use 'inurl:' to search in the URL only. E.g., inurl:climate
        10. All In Text: Use 'allintext:' to require all words in the body text. E.g., allintext:climate change

        Examples:
        - "artificial intelligence" site:techcrunch.com when:1d
        - Tesla OR "electric vehicles" -SpaceX after:2023-01-01
        - location:"San Francisco" tech intitle:startup
        """
        return explanation

    async def download_news_article(self, title: str, url: str) -> str:
        """Resolves internal Google News links to the actual news article links."""

        try:
            if "news.google.com" in url:
                decoded_url = new_decoderv1(url, interval=1)
                if decoded_url.get("status"):
                    url = decoded_url["decoded_url"]
                else:
                    return (
                        f"Error resolving actual article link: {decoded_url['message']}"
                    )

            url_titles = [(url, title)]
            text_results = await self.browser_tool.convert_downloaded_pages(
                url_titles, 5000
            )
            return "\n".join(text_results)

        except Exception as e:
            print(f"News page download error occurred: {e}")
            return "Error downloading page"
