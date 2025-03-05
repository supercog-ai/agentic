from typing import Generator, Any, Optional, Dict
from .actor_agents import RayFacadeAgent
from .events import Event, Prompt, ChatOutput, FinishCompletion, TurnEnd
from .common import Agent
from .models import GPT_4O_MINI

class LangChainWrapperAgent(RayFacadeAgent):
    """
    A wrapper agent for LangChain agents that integrates them into the Agentic framework.
    
    This agent allows LangChain agents to be used within the Agentic ecosystem by:
    1. Converting Agentic prompts to LangChain inputs
    2. Running the LangChain agent
    3. Converting LangChain outputs to Agentic events
    """
    
    def __init__(
        self, 
        name: str = "LangChain Agent", 
        model: str = GPT_4O_MINI,
        langchain_agent = None
    ):
        """
        Initialize the LangChain wrapper agent.
        
        Args:
            name: The name of the agent
            model: The model to use for the agent
            langchain_agent: The LangChain agent to wrap
        """
        super().__init__(
            name, 
            welcome=f"I am the {name}, powered by LangChain.",
            model=model,
        )
        self.langchain_agent = langchain_agent
        
    def next_turn(
        self,
        request: str | Prompt,
        request_context: dict = {},
        request_id: str = None,
        continue_result: dict = {},
        debug = "",
    ) -> Generator[Event, Any, Any]:
        """
        Process a turn with the LangChain agent.
        
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
        query = request.payload if isinstance(request, Prompt) else request
        
        # Yield a chat output to show we're processing
        yield ChatOutput(self.name, {"content": f"Processing query: {query}"})
        
        # If we have a LangChain agent, run it
        if self.langchain_agent:
            try:
                # Run the LangChain agent
                result = self.langchain_agent.run(query)
                
                # Yield the result as a chat output
                yield ChatOutput(self.name, {"content": result})
                
                # Return the final result
                messages = [{"role": "assistant", "content": result}]
                yield TurnEnd(
                    self.name,
                    messages,
                    self.run_context,
                    self.depth
                )
                return result
            except Exception as e:
                error_message = f"Error running LangChain agent: {str(e)}"
                yield ChatOutput(self.name, {"content": error_message})
                messages = [{"role": "assistant", "content": error_message}]
                yield TurnEnd(
                    self.name,
                    messages,
                    self.run_context,
                    self.depth
                )
                return error_message
        else:
            error_message = "No LangChain agent provided."
            yield ChatOutput(self.name, {"content": error_message})
            messages = [{"role": "assistant", "content": error_message}]
            yield TurnEnd(
                self.name,
                messages,
                self.run_context,
                self.depth
            )
            return error_message
