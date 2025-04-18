from typing import Callable
from urllib.parse import urlparse
import httpx
import aiofiles
import html2text
import requests

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry

@tool_registry.register(
    name="FileDownloadTool",
    description="Download files from the internet",
    dependencies=[],
    config_requirements=[],
)

class FileDownloadTool(BaseAgenticTool):
    def __init__(self):
        super().__init__()

    def get_tools(self) -> list[Callable]:
        return [
            self.download_url_as_file,
            self.download_file_content,
        ]

    async def _download_url_as_file(
        self, url: str, file_name_hint: str = ""
    ) -> tuple[str, str]:
        # Returns the saved file name, and the original URL mime type
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await client.get(url)
            save_file = file_name_hint or self.get_last_path_component(url)

            if r.status_code == 200:
                mime_type = r.headers.get("content-type", "").split(";")[0]

                async with aiofiles.open(save_file, "wb") as f:
                    async for chunk in r.aiter_bytes(chunk_size=8192):
                        if chunk:
                            await f.write(chunk)
                return save_file, mime_type
            else:
                raise ValueError(f"Error: {r.status_code} {r.text}")

    async def download_url_as_file(self, url: str, file_name_hint: str = "") -> str:
        """Downloads a file from the web and stores it locally. Returns the
        file name.
        """
        try:
            save_file, mime_type = await self._download_url_as_file(url, file_name_hint)
            return save_file
        except ValueError as e:
            return str(e)

    def get_last_path_component(self, url: str) -> str:
        # Parse the URL
        parsed_url = urlparse(url)
        # Get the path from the parsed URL
        path = parsed_url.path
        # Split the path and get the last component
        last_component = path.split("/")[-1]
        if not last_component.strip():
            last_component = "_".join(path.strip("/").split("/"))
            if not last_component:
                last_component = parsed_url.hostname or "download"

        return last_component

    def download_file_content(self, url: str, limit: int = 4000) -> str:
        """Downloads a file from the web and returns its contents directly."""
        r = requests.get(url)

        if r.status_code == 200:
            mime_type = r.headers.get("content-type") or ""
            if "html" in mime_type:
                # Use beautifulsoup to extract text
                return html2text.html2text(r.text)[0:limit]
            else:
                return r.text[0:limit]
        else:
            return f"Error: {r.status_code} {r.reason}"
