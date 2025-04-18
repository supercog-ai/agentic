import time
from typing import Callable, List
from playwright.sync_api import sync_playwright, Browser, Page

from agentic.tools.base import BaseAgenticTool
from agentic.tools.utils.registry import tool_registry, Dependency
from agentic.common import RunContext

@tool_registry.register(
    name="PlaywrightTool",
    description="Tool for browser automation using Playwright.",
    dependencies=[
        Dependency(
            name="playwright",
            version="1.51.0",
            type="pip",
        ),
    ],
    config_requirements=[],
)

class PlaywrightTool(BaseAgenticTool):
    """Tool for browser automation using Playwright."""
    
    _browser: Browser = None
    _page: Page = None
    _playwright = None
    
    def __init__(self, headless: bool = False):
        """Initialize the browser automation tool.
        
        Args:
            headless: Whether to run browser in headless mode. Defaults to False (visible).
        """
        self.headless = headless

    def __del__(self):
        """Cleanup browser resources."""
        if hasattr(self, "_browser") and self._browser:
            self._browser.close()
        if hasattr(self, "_playwright") and self._playwright:
            self._playwright.stop()

    def _get_browser(self):
        if hasattr(self, "_playwright") and self._playwright:
            return
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._page = self._browser.new_page()

    def close_browser(self):
        if hasattr(self, "_browser") and self._browser:
            self._browser.close()
            self._browser = None
        if hasattr(self, "_playwright") and self._playwright:
            self._playwright.stop()
            self._playwright = None

    def get_tools(self) -> List[Callable]:
        return [
            self.navigate_to_url,
            self.extract_text,
            self.take_screenshot,
            self.click_element
        ]

    def navigate_to_url(self, run_context: RunContext, url: str) -> str:
        """Navigate to a URL and return the page title."""
        self._get_browser()
        try:
            # First navigate to the URL without waiting
            response = self._page.goto(url, timeout=3000)
            try:
                self._page.wait_for_load_state("load", timeout=8000)
            except:
                print("Wait for page load exceeded 8 seconds, returning anyway")
                pass # ignore timeout
            title = self._page.title()
            print("Returning title: ", title)
            return title
        except Exception as e:
            return None #return f"Failed to navigate to {url}: {str(e)}"
    
    def extract_text(self, run_context: RunContext, selector: str, convert_to_markdown: bool = True) -> str:
        """Extract text content from elements matching a CSS selector."""
        self._get_browser()
        try:
            elements = self._page.query_selector_all(selector, timeout=8000)
            if not elements:
                return "No elements found"
            
            if convert_to_markdown:
                # Import html2text for HTML to Markdown conversion
                try:
                    import html2text
                except ImportError:
                    return "html2text module not installed. Please install with: pip install html2text"
                
                # Get HTML content
                html_contents = []
                for element in elements:
                    html_content = element.evaluate("el => el.outerHTML")
                    if html_content:
                        html_contents.append(html_content)
                
                if not html_contents:
                    return "No HTML content found"
                
                # Configure html2text
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = False
                h.ignore_tables = False
                
                # Convert to markdown
                markdown_texts = [h.handle(html) for html in html_contents]
                return "\n\n".join(markdown_texts)
            else:
                # Original behavior - extract plain text
                texts = [el.text_content() for el in elements]
                return "\n".join(texts)
        except Exception as e:
            return f"Failed to extract text: {str(e)}"
        
    def take_screenshot(
        self, 
        run_context: RunContext, 
        selector: str = None,
        filename: str = None
    ) -> str:
        """Take a screenshot of the page or a specific element.
        
        Args:
            selector: Optional CSS selector to screenshot specific element
            filename: Optional filename to save screenshot (defaults to timestamp)
        Returns:
            Path to saved screenshot file
        """
        self._get_browser()
        try:
            if not filename:
                filename = f"screenshot_{int(time.time())}.png"
            
            if selector:
                element = self._page.query_selector(selector)
                if not element:
                    return "Element not found"
                element.screenshot(path=filename)
            else:
                self._page.screenshot(path=filename, full_page=True)
                
            return f"Screenshot saved to {filename}"
        except Exception as e:
            return f"Failed to take screenshot: {str(e)}"

    def click_element(self, run_context: RunContext, selector: str) -> str:
        """Click an element matching the CSS selector.
        
        Args:
            selector: CSS selector for element to click
        Returns:
            Success/failure message
        """
        self._get_browser()
        try:
            element = self._page.query_selector(selector)
            if not element:
                return f"No element found matching selector: {selector}"
            element.click()
            return f"Successfully clicked element: {selector}"
        except Exception as e:
            return f"Failed to click element: {str(e)}"

    def download_pages(self, run_context: RunContext, pages: List[str]) -> list[tuple[str, str, str]]:
        # Downloads the content of the indicated pages. Returns
        # a list of results tuples (url, title, content). Content and title may be None if 
        # we could not retrieve a page.
        # This function is meant to be called with a batch of links. It will open the browser
        # and then close it when it's done.
        results = []
        for page in pages:
            print("[playwright navigate] ", page)
            title = self.navigate_to_url(run_context, page)
            if title:
                print(f"[playwright extract] {title}")
                page_content = self.extract_text(run_context, page)
                results.append((page, title, page_content))
            else:
                results.append((page, None, None))
        self.close_browser()
        return results