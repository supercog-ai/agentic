from typing import Optional, Dict, Callable
from uuid import uuid4
from litellm import Message
from .events import (
    Event,
    PromptStarted,
    Output,
    TurnEnd,
    FinishCompletion,
    ToolCall,
    ToolResult,
    ToolError
)
from agentic.common import RunContext
from agentic.utils.json import make_json_serializable
from agentic.db.db_manager import DatabaseManager
from agentic.utils.directory_management import get_runtime_filepath

class RunManager:
    """
    Context manager that tracks agent runs and logs events to the database.
    This is automatically initialized for all agents unless disabled with db_path=None.
    """
    
    def __init__(self, initial_run_id: Optional[str] = None, current_run_id: Optional[str] = None, user_id: str = "default", db_path: str = "agent_runs.db"):
        self.user_id = user_id
        self.initial_run_id: Optional[str] = initial_run_id
        self.current_run_id: Optional[str] = current_run_id
        # Should this not be propagated from the next_turn?
        self.usage_data: Dict = {}
        self.db_path = get_runtime_filepath(db_path)
    
    def handle_event(self, event: Event, run_context: RunContext) -> None:
        """Generic event handler that processes all events and logs them appropriately"""
        db_manager = DatabaseManager(db_path=self.db_path)
        # Initialize a new run when we see a Prompt event

        if isinstance(event, PromptStarted) and not self.current_run_id:
            if type(event.payload)==dict:
                prompt = event.payload['content']
            else:
                prompt = str(event.payload)
            run = db_manager.create_run(
                run_id=self.initial_run_id,
                agent_id=run_context.agent_name,
                user_id=self.user_id,
                initial_prompt=prompt
            )
            self.current_run_id = run.id
            run_context.run_id = run.id 
            
        self.current_run_id = run_context.run_id
        if not self.current_run_id:
            run_context.run_id = self.initial_run_id
            self.current_run_id = self.initial_run_id
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
        
        if isinstance(event, Output):
            event_data = payload
        
        elif isinstance(event, ToolCall) or isinstance(event, ToolResult) or isinstance(event, ToolError):
            role = "tool"
            event_data = make_json_serializable(payload)
            
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

def init_run_tracking(
        agent,
        user_id: str|None = "default",
        db_path: str = "agent_runs.db",
        resume_run_id: Optional[str] = None
    ) -> tuple[str,Callable]:
    """Helper function to set up run tracking for an agent"""
    run_id = str(uuid4()) if resume_run_id is None else resume_run_id
    user_id = user_id or "default"
    run_manager = RunManager(
        initial_run_id=run_id,
        current_run_id=resume_run_id,
        user_id=user_id,
        db_path=db_path
    )
    return run_id, run_manager.handle_event

def disable_run_tracking(agent) -> None:
    """Helper function to disable run tracking for an agent"""
    raise NotImplemented("Can't disable run tracking from outside the proxy")