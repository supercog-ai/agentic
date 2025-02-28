# pip install playwright
# pip install browser-use
from typing import Optional, Generator, Any
import asyncio

from agentic.tools import tool_registry
from agentic.models import GPT_4O_MINI
from agentic.common import RunContext, Agent
from agentic.events import Event, Prompt, ChatOutput, FinishCompletion, TurnEnd
from agentic.actor_agents import RayFacadeAgent
from browser_use import Agent as BrowserAgent
from browser_use import Browser, BrowserConfig
from langchain_openai import ChatOpenAI
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
class BrowserUseTool:
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
    
    # Yield strings of browser actions
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
            browser = browser = Browser(
                config=BrowserConfig(
                    chrome_instance_path=self.chrome_instance_path
                )
            )
        token_counter = TokenCounterStdOutCallback()
        if self.model.startswith("gemini"):
            llm = ChatGoogleGenerativeAI(model=self.model.split("/")[-1], callbacks=[token_counter])
        else:
            llm = ChatOpenAI(model=self.model, callbacks=[token_counter])

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


class BrowserUseAgent(RayFacadeAgent):
    """
    An agent that wraps the BrowserUseTool to provide browser automation capabilities.
    
    This agent can be used directly as a tool in other agents:
    operator = Agent(name="Operator", tools=[BrowserUseAgent()])
    """
    
    def __init__(
        self, 
        name: str = "Browser Agent", 
        chrome_instance_path: Optional[str] = None,
        model: str = GPT_4O_MINI
    ):
        """
        Initialize the Browser Use Agent.
        
        Args:
            name: The name of the agent
            chrome_instance_path: Optional path to Chrome executable
            model: The model to use for the agent
        """
        super().__init__(
            name, 
            welcome=f"I am the {name}, capable of automating browser interactions.",
            model=model,
        )
        self.chrome_instance_path = chrome_instance_path
        self.browser_tool = BrowserUseTool(chrome_instance_path, model)
        
    def next_turn(
        self,
        request: str | Prompt,
        request_context: dict = {},
        request_id: str = None,
        continue_result: dict = {},
        debug = "",
    ) -> Generator[Event, Any, Any]:
        """
        Process a turn with the Browser agent.
        
        Args:
            request: The prompt or string request
            request_context: Additional context for the request
            request_id: Optional request ID
            continue_result: Results to continue from
            debug: Debug level
            
        Yields:
            Event: Agentic events representing the agent's processing
        """
        # Convert request to string if it's a Prompt
        instructions = request.payload if isinstance(request, Prompt) else request
        
        # Yield a chat output to show we're processing
        yield ChatOutput(self.name, {"content": f"Processing browser instructions: {instructions}"})
        
        try:
            # Create browser configuration
            browser = None
            if self.chrome_instance_path:
                browser = Browser(
                    config=BrowserConfig(
                        chrome_instance_path=self.chrome_instance_path
                    )
                )
            
            # Set up token counter
            token_counter = TokenCounterStdOutCallback()
            
            # Set up LLM based on model type
            if self.model.startswith("gemini"):
                llm = ChatGoogleGenerativeAI(model=self.model.split("/")[-1], callbacks=[token_counter])
            else:
                llm = ChatOpenAI(model=self.model, callbacks=[token_counter])
            
            # Create and run browser agent
            browser_agent = BrowserAgent(   
                task=instructions,
                llm=llm,
                browser=browser,
            )
            
            # Yield a message that we're running the browser agent
            yield ChatOutput(self.name, {"content": "Running browser automation..."})
            
            # Run the browser agent
            result = asyncio.run(browser_agent.run())
            
            # Extract content from result
            content = "\n".join(result.extracted_content())
            
            # Yield the content as a chat output
            yield ChatOutput(self.name, {"content": content})
            
            # Yield token usage information
            yield FinishCompletion.create(
                agent=self.name,
                llm_message=f"Tokens used - Input: {token_counter.total_input_tokens}, Output: {token_counter.total_output_tokens}",
                model=self.model,
                cost=0,
                input_tokens=token_counter.total_input_tokens,
                output_tokens=token_counter.total_output_tokens,
                elapsed_time=0,
                depth=self.depth,
            )
            
            # Return the final result
            messages = [{"role": "assistant", "content": content}]
            yield TurnEnd(
                self.name,
                messages,
                self.run_context,
                self.depth
            )
            return content
            
        except Exception as e:
            error_message = f"Error running browser automation: {str(e)}"
            yield ChatOutput(self.name, {"content": error_message})
            messages = [{"role": "assistant", "content": error_message}]
            yield TurnEnd(
                self.name,
                messages,
                self.run_context,
                self.depth
            )
            return error_message
    
    def get_tools(self):
        """Return the browser tools for use in other agents."""
        return self.browser_tool.get_tools()
