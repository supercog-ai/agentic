from typing import Optional, Dict
from litellm import Message
from .events import (
    Event,
    PromptStarted,
    TurnEnd,
    FinishCompletion,
    ToolCall,
    ToolResult
)
from .common import Agent, RunContext
from agentic.utils.sqlite import make_json_serializable

class RunManager:
    """
    Context manager that tracks agent runs and logs events to the database.
    This is automatically initialized for all agents unless disabled with enable_run_tracking=False.
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.current_run_id: Optional[int] = None
        self.usage_data: Dict = {}
    
    def handle_event(self, event: Event, run_context: RunContext) -> None:
        """Generic event handler that processes all events and logs them appropriately"""
        from agentic.db.db_manager import db_manager
        
        # Initialize a new run when we see a Prompt event
        # TODO: Handle multiple prompts in a single run
        if isinstance(event, PromptStarted):
            run = db_manager.create_run(
                agent_id=run_context.agent_name,
                user_id=self.user_id,
                initial_prompt=event.payload,
            )
            self.current_run_id = run.id
            
        # Skip if we haven't initialized a run yet
        if not self.current_run_id:
            return
            
        # Special handling for completion events to track usage
        if isinstance(event, FinishCompletion) and event.metadata:
            model = event.metadata.get(FinishCompletion.MODEL_KEY, "unknown")
            if model not in self.usage_data:
                self.usage_data[model] = {
                    FinishCompletion.INPUT_TOKENS_KEY: 0,
                    FinishCompletion.OUTPUT_TOKENS_KEY: 0,
                    FinishCompletion.COST_KEY: 0
                }
            self.usage_data[model][FinishCompletion.INPUT_TOKENS_KEY] += event.metadata.get(FinishCompletion.INPUT_TOKENS_KEY, 0)
            self.usage_data[model][FinishCompletion.OUTPUT_TOKENS_KEY] += event.metadata.get(FinishCompletion.OUTPUT_TOKENS_KEY, 0)
            self.usage_data[model][FinishCompletion.COST_KEY] += event.metadata.get(FinishCompletion.COST_KEY, 0)
            
        # Determine role and event data based on event type
        role = event.payload.role if isinstance(event.payload, Message) else "system"
        event_name = event.type
        payload = event.payload.content if isinstance(event.payload, Message) else event.payload
        event_data = {"content": payload} if payload else {}
        
        if isinstance(event, ToolCall):
            role = "tool"
            event_data = {
                "name": payload,
                "arguments": make_json_serializable(event.args)
            }
            
        elif isinstance(event, ToolResult):
            role = "tool"
            event_data = {
                "name": payload,
                "result": make_json_serializable(event.result)
            }
            
        elif isinstance(event, FinishCompletion):
            role = "usage"
            event_data = {
                "usage": self.usage_data
            }

        elif isinstance(event, TurnEnd):
            event_data = {}
            
        # Log the event
        db_manager.log_event(
            run_id=self.current_run_id,
            agent_id=run_context.agent_name,
            user_id=self.user_id,
            role=role,
            event_name=event_name,
            event_data=event_data
        )
        
        # Reset usage tracking after a turn ends
        if isinstance(event, TurnEnd):
            self.usage_data = {}

def init_run_tracking(agent: Agent, user_id: str = "default") -> RunManager:
    """Helper function to set up run tracking for an agent"""
    run_manager = RunManager(user_id)
    agent._agent.set_callback.remote('handle_event', run_manager.handle_event)
    return run_manager

def disable_run_tracking(agent: Agent) -> None:
    """Helper function to disable run tracking for an agent"""
    if agent._agent.get_callback.remote('handle_event'):
        agent._agent.set_callback.remote('handle_event', None)