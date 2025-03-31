# pip install playwright
# pip install browser-use
from typing import Optional
import os

from agentic.tools.utils.registry import tool_registry
from agentic.models import GPT_4O_MINI
from agentic.common import RunContext
from agentic.events import FinishCompletion
from agentic.tools.base import BaseAgenticTool
from browser_use import Agent as BrowserAgent
from browser_use import Browser, BrowserConfig
from langchain.callbacks import StdOutCallbackHandler
from langchain_google_genai import ChatGoogleGenerativeAI

@tool_registry.register(
    name="Browser-use Tool",
    description="Automate browser interactions with a smart agent. https://docs.browser-use.com/",
    dependencies=[
        tool_registry.Dependency(
            name="playwright",
            version="1.50.0",
            type="pip",
        ),
        tool_registry.Dependency(
            name="browser-use",
            version="0.1.37",
            type="pip",
        ),
    ],
)
class BrowserUseTool(BaseAgenticTool):
    # Automates browser interactions with a smart agent.
    # Set the chrome_instance_path to the path to your Chrome executable if you want to use YOUR browser with its
    # cookies and state - but be careful.
    #
    # Typical paths:
    # For MacOS: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 
    # For Windows, typically: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
    # For Linux, typically: '/usr/bin/google-chrome'

    # FIXME: Check the model and make sure we have the API key (implement "required_secrets").
    
    def __init__(self, chrome_instance_path: Optional[str]=None, model: str=GPT_4O_MINI):
        self.chrome_instance_path = chrome_instance_path
        self.model = model

    def get_tools(self):
        return [self.run_browser_agent]
    
    def _get_api_key(self, model: str) -> str:
        """Get the appropriate API key based on model type."""
        from agentic.agentic_secrets import agentic_secrets
        
        if model.startswith("gemini"):
            return agentic_secrets.get_required_secret("GEMINI_API_KEY")
        elif model.startswith("gpt") or model.startswith("openai"):
            return agentic_secrets.get_required_secret("OPENAI_API_KEY")
        elif model.startswith("anthropic") or model.startswith("claude"):
            return agentic_secrets.get_required_secret("ANTHROPIC_API_KEY")
        else:
            # For other models, try to infer the API key name
            provider = model.split("/")[0] if "/" in model else model.split("-")[0]
            key_name = f"{provider.upper()}_API_KEY"
            return agentic_secrets.get_required_secret(key_name)
    
    def _initialize_llm(self, model: str):
        """Initialize LLM based on model path string."""
        api_key = self._get_api_key(model)
        
        if model.startswith("gemini"):
            model_name = model.split("/")[-1] if "/" in model else model
            return ChatGoogleGenerativeAI(model=model_name, api_key=api_key)
        else:
            # For other models, use Litellm's completion
            from litellm import completion
            os.environ["OPENAI_API_KEY"] = api_key  # Ensure API key is set for Litellm
            return completion

    async def run_browser_agent(
            self, 
            run_context: RunContext,
            instructions: str,
            model: Optional[str] = None
    ) -> list[str|FinishCompletion]:
        """ Execute a set of instructions via browser automation. Instructions can be in natural language. 
            The history of browsing actions taken is returned.
        """
        browser = None
        print(f"BrowserTool, Using model: {self.model}")
        if self.chrome_instance_path:
            browser = Browser(
                config=BrowserConfig(
                    chrome_instance_path=self.chrome_instance_path
                )
            )
        
        token_counter = TokenCounterStdOutCallback()
        llm = self._initialize_llm(model or self.model)

        agent = BrowserAgent(   
            task=instructions,
            llm=llm,
            browser=browser,
        )
        result = await agent.run()
        return [
            "\n".join(result.extracted_content()),
            FinishCompletion.create(
                agent=run_context.agent.name,
                llm_message=f"Tokens used - Input: {token_counter.total_input_tokens}, Output: {token_counter.total_output_tokens}",
                model=self.model,
                cost=0,
                input_tokens=token_counter.total_input_tokens,
                output_tokens=token_counter.total_output_tokens,
                elapsed_time=0,
                depth=0,
            )
        ]
    


class TokenCounterStdOutCallback(StdOutCallbackHandler):
    def __init__(self):
        super().__init__()
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def on_llm_end(self, response, **kwargs):
        if hasattr(response, "llm_output") and response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})
            input_tokens = token_usage.get("prompt_tokens", 0)
            output_tokens = token_usage.get("completion_tokens", 0)

            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens

            print(f"[AGENTIC] Tokens used - Input: {input_tokens}, Output: {output_tokens}")
            print(f"[AGENTIC] Total tokens - Input: {self.total_input_tokens}, Output: {self.total_output_tokens}")
        else:
            print("[AGENTIC] No token usage data available.")

