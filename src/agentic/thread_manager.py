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
from agentic.common import ThreadContext
from agentic.utils.json import make_json_serializable
from agentic.db.db_manager import DatabaseManager
from agentic.utils.directory_management import get_runtime_filepath

class ThreadManager:
    """
    Context manager that tracks agent threads and logs events to the database.
    This is automatically initialized for all agents unless disabled with db_path=None.
    """
    
    def __init__(self, initial_thread_id: Optional[str] = None, db_path: str = "agent_threads.db"):
        self.initial_thread_id: Optional[str] = initial_thread_id
        # Should this not be propagated from the next_turn?
        self.usage_data: Dict = {}
        self.db_path = get_runtime_filepath(db_path)
    
    def handle_event(self, event: Event, thread_context: ThreadContext) -> None:
        """Generic event handler that processes all events and logs them appropriately"""
        db_manager = DatabaseManager(db_path=self.db_path)
        # Initialize a new thread when we see a Prompt event

        if isinstance(event, PromptStarted):
            if type(event.payload)==dict:
                prompt = event.payload['content']
            else:
                prompt = str(event.payload)

            # Check if the thread is in the database
            thread = db_manager.get_thread(thread_id=self.initial_thread_id)
            if not thread:
                thread = db_manager.create_thread(
                    thread_id=self.initial_thread_id,
                    agent_id=thread_context.agent_name,
                    user_id=str(thread_context.get("user") or "default"),
                    initial_prompt=prompt,
                )
            thread_context.thread_id = thread.id 
            
        self.current_thread_id = thread_context.thread_id
        if not self.current_thread_id:
            thread_context.thread_id = self.initial_thread_id
            self.current_thread_id = self.initial_thread_id
        # Skip if we haven't initialized a thread yet
        if not thread_context.thread_id:
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
            thread_id=thread_context.thread_id,
            agent_id=thread_context.agent_name,
            user_id=str(thread_context.get("user") or "default"),
            role=role,
            event_name=event_name,
            event_data=event_data
        )
        
        # Reset usage tracking after a turn ends
        if isinstance(event, TurnEnd):
            self.usage_data = {}

def init_thread_tracking(
        agent,
        db_path: str = "agent_threads.db",
        resume_thread_id: Optional[str] = None
    ) -> tuple[str,Callable]:
    """Helper function to set up thread tracking for an agent"""
    thread_id = str(uuid4()) if resume_thread_id is None else resume_thread_id
    thread_manager = ThreadManager(
        initial_thread_id=thread_id,
        db_path=db_path
    )
    return thread_id, thread_manager.handle_event

def disable_thread_tracking(agent) -> None:
    """Helper function to disable thread tracking for an agent"""
    raise NotImplemented("Can't disable thread tracking from outside the proxy")