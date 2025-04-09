import asyncio
from typing import Generator, Any
from pydantic import BaseModel, Field
from datetime import datetime

from agentic.common import Agent, AgentRunner, RunContext
from agentic.events import Prompt, TurnEnd, ChatOutput, WaitForInput, PromptStarted, Event

class DummyResearchAgent(Agent):
    """
    Simplified version of DeepResearchAgent for testing run logging functionality.
    This agent does minimal work but yields various events that should be logged.
    """
    
    def __init__(self, name: str="Dummy Research Agent", model: str="gpt-4o-mini", verbose: bool = True):
        super().__init__(
            name, 
            welcome="I am a dummy research agent for testing run logging.",
            model=model,
        )
        self.verbose = verbose
        
    def _next_turn(
        self,
        request: str|Prompt,
        request_context: dict = {},
        request_id: str = None,
        continue_result: dict = {},
        debug = "",
    ) -> Generator[Event, Any, Any]:
        """
        Simplified implementation that yields various events to test logging.
        """
        topic = request.payload if isinstance(request, Prompt) else request
        yield PromptStarted(self.name, {"content": f"Researching: {topic}"})
        yield ChatOutput(self.name, {"content": f"Starting research on: {topic}"})
        if continue_result:
            feedback = continue_result.get("feedback", "")
            yield ChatOutput(self.name, {"content": f"Received feedback: {feedback}"})
        else:
            yield WaitForInput(
               self.name, 
               {"feedback": f"How would you like me to research '{topic}'?"}
            )
            return
        yield ChatOutput(self.name, {"content": "Performing research..."})
        await_sleep(1)
        report = f"# Research Report on {topic}\n\n"
        report += "## Summary\n\n"
        report += f"This is a dummy report on {topic} created at {datetime.now().isoformat()}"
        
        yield ChatOutput(self.name, {"content": report})
        yield TurnEnd(
            self.name,
            [{"role": "assistant", "content": report}],
            run_context=RunContext(self.name),
        )

def await_sleep(seconds):
    """Non-blocking sleep function that works with generators"""
    try:
        asyncio.sleep(seconds)
    except:
        pass

dummy_researcher = DummyResearchAgent(name="Dummy Research Agent")

if __name__ == "__main__":
    AgentRunner(dummy_researcher).repl_loop()