import asyncio
import os
import re
import html2text
import httpx
from typing import Callable

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry

@tool_registry.register(
    name="ScaleSerpBrowserTool",
    description="Browse the web using ScaleSerp",
    dependencies=[],
    config_requirements=[],
)

class ScaleSerpBrowserTool(BaseAgenticTool):
    def __init__(self):
        super().__init__()

    def get_tools(self) -> list[Callable]:
        return [
            self.browse_web_tool,
            self.download_web_pages,
        ]

    @staticmethod
    async def try_scrapingbee(search: str) -> list[tuple[str, str]]:
        url = "https://app.scrapingbee.com/api/v1/store/google"
        params = {
            "api_key": os.environ.get("SCRAPINGBEE_API_KEY"),
            "search": search,
            "language": "en",
            "nb_results": 8,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                timeout=90,
            )
            results = response.json()
            if "organic_results" not in results:
                return []
            else:
                return [
                    (serp["url"], serp["title"])
                    for serp in results["organic_results"][0:5]
                ]

    async def browse_web_tool(
        self,
        search: str,
    ):
        """Browses the web using the SCALESERP API and returns full page contents related to the search term."""
        api_key: str | None = os.environ.get("SCALESERP_API_KEY")
        if api_key is None:
            return "Error: no API key available for the SCALE SERP API"

        urls: list[tuple] = []
        if search is not None:
            m = re.match(r"site:([\S]+)", search)
            if m:
                urls.append((m.group(1), ""))
            else:
                params = {
                    "q": search,
                    "location": "San Francisco, California, United States",
                    "timeout": 10000,
                    "num": 8,
                    "api_key": api_key,
                }
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            "https://api.scaleserp.com/search",
                            params=params,
                            timeout=90,
                        )
                        results = response.json()

                        if "organic_results" not in results:
                            return "ScaleSerp return no results."

                        for serp in results["organic_results"][0:5]:
                            urls.append((serp["link"], serp["title"]))
                except httpx.TimeoutException:
                    # Let's try Scrapingbee
                    print("Timed out! Fallback to ScrapingBee")
                    urls.extend(await ScaleSerpBrowserTool.try_scrapingbee(search))

                # FIXME: Download pages in parallel

        text_results = [f"search: {search}"]
        used = len(text_results[-1])
        max_count = 10000  # need to know actual token limit
        text_results.extend(await self.convert_downloaded_pages(urls[0:4], max_count))

        # FIXME: Download pages in parallel
        used = len(text_results[-1])

        return "\n".join(text_results)

    async def download_web_pages(self, page_urls: list[str] = []) -> str:
        """Returns the contents of one or more web pages. Text is extracted from HTML pages."""
        url_titles = [(url, url[0:40]) for url in page_urls]
        text_results = await self.convert_downloaded_pages(url_titles, 10000)
        return "\n".join(text_results)

    async def convert_downloaded_pages(
        self, url_titles: list[tuple], max_count: int
    ) -> list[str]:
        used = 0
        text_results = []
        for res_dict in await self.download_pages(url_titles):
            if "content" in res_dict:
                text_results.append(
                    f"PAGE: {res_dict['title']} (url: {res_dict['url']})"
                )
                used += len(text_results[-1])
                remaining = max_count - used
                if remaining > 0:
                    text_results.append(
                        html2text.html2text(res_dict["content"])[0:remaining]
                    )
                else:
                    break
                used += len(text_results[-1])
                text_results.append("-----")
        return text_results

    async def download_pages(
        self, url_titles: list[tuple], max_concurrency=10
    ) -> list[dict]:
        async with httpx.AsyncClient() as client:
            sem = asyncio.Semaphore(max_concurrency)

            async def bounded_fetch(client, url, title):
                async with sem:
                    return await self.download_page(client, url, title)

            tasks = [bounded_fetch(client, url[0], url[1]) for url in url_titles]
            results = await asyncio.gather(*tasks)

        return results

    async def download_page(self, client, url, title) -> dict:
        try:
            if not url.startswith("http"):
                url = "https://" + url
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return {"url": url, "title": title, "content": response.content.decode()}

        except httpx.HTTPError as e:
            print(f"HTTP Error for {url}: {e}")
            return {"url": url, "title": title, "error": str(e)}
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return {"url": url, "title": title, "error": str(e)}
