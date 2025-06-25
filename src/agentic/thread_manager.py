import json
from typing import Optional, Dict, Callable, Any, List
from uuid import uuid4
from litellm import Message
import traceback
from .events import (
    Event,
    PromptStarted,
)
from agentic.common import ThreadContext
from agentic.db.models import ThreadLog
from agentic.db.db_manager import DatabaseManager
from agentic.events import ChatOutput
from agentic.event_factory import EventFactory
from agentic.utils.directory_management import get_runtime_filepath

class ThreadManager:
    """
    Context manager that tracks agent threads and logs events to the database.
    This is automatically initialized for all agents unless disabled with db_path=None.
    """
    
    def __init__(self, initial_thread_id: Optional[str] = None, db_path: str = "agent_threads.db"):
        self.initial_thread_id: Optional[str] = initial_thread_id
        # Should this not be propagated from the next_turn?
        self.db_path = get_runtime_filepath(db_path)
        self.db_manager = DatabaseManager(db_path=self.db_path)
    
    def handle_event(self, event: Event, thread_context: ThreadContext) -> None:
        """Generic event handler that processes all events and logs them appropriately"""
       # Initialize thread on first prompt
        if isinstance(event, PromptStarted):
            prompt = event.payload["content"] if isinstance(event.payload, dict) else str(event.payload)
            thread = self.db_manager.get_thread(thread_id=self.initial_thread_id)
            if not thread:
                thread = self.db_manager.create_thread(
                    thread_id=self.initial_thread_id,
                    agent_id=thread_context.agent_name,
                    user_id=str(thread_context.get("user") or "default"),
                    initial_prompt=prompt,
                )
            thread_context.thread_id = thread.id
        
        # Skip if no thread initialized
        if not thread_context.thread_id:
            return
        
        # Determine role and event data based on event type
        role = event.payload.role if isinstance(event.payload, Message) else "system"
        
        # Just dump the entire event as JSON
        try:
            self.db_manager.log_event(
                thread_id=thread_context.thread_id,
                agent_id=thread_context.agent_name,
                user_id=str(thread_context.get("user") or "default"),
                role=role,
                depth=event.depth,
                event_name=event.type,
                event_data=event.payload
            )
        except Exception as e:
            traceback.print_exc()
            print(f"Error logging event {event.type} for thread {thread_context.thread_id}: {e}.")

def init_thread_tracking(
        agent,
        db_path: str = "agent_threads.db",
        resume_thread_id: Optional[str] = None
    ) -> tuple[str,Callable]:
    """Helper function to set up thread tracking for an agent"""
    thread_id = str(uuid4()) if (resume_thread_id is None or resume_thread_id == 'NEW') else resume_thread_id
    thread_manager = ThreadManager(
        initial_thread_id=thread_id,
        db_path=db_path
    )
    return thread_id, thread_manager.handle_event

def load_thread_history(thread_id: str) -> list[Any]:
    return []

def disable_thread_tracking(agent) -> None:
    """Helper function to disable thread tracking for an agent"""
    raise NotImplemented("Can't disable thread tracking from outside the proxy")

# Below is Claude-generated code for reconstructing chat history from thread logs

def reconstruct_chat_history_from_thread_logs(thread_logs: List[ThreadLog]) -> List[Dict[str, Any]]:
    """
    Reconstruct LLM chat history from ThreadLog database records.
    
    Args:
        thread_logs: List of ThreadLog objects from the database
        
    Returns:
        List of chat messages in the format expected by the LLM
    """
    history = []
    current_assistant_message = None
    
    for log in thread_logs:
        event = EventFactory.from_thread_log(log)
        if event:
            llm_message = event.to_llm_message()
            if llm_message:
                # Compile chat outputs
                if isinstance(event, ChatOutput):
                    if current_assistant_message:
                        current_assistant_message["content"] += llm_message["content"]
                    else:
                        current_assistant_message = llm_message
                else:
                    if current_assistant_message:
                        history.append(current_assistant_message)
                        current_assistant_message = None

                    history.append(llm_message)
    
    return history

# NOT USED YET
def reconstruct_chat_history_with_filtering(
    thread_logs: List[ThreadLog], 
    include_usage: bool = False,
    include_system_events: bool = False
) -> List[Dict[str, Any]]:
    """
    Reconstruct chat history with optional filtering of event types.
    
    Args:
        thread_logs: List of ThreadLog objects from the database
        include_usage: Whether to include usage/cost tracking events
        include_system_events: Whether to include system/debug events
        
    Returns:
        List of chat messages in the format expected by the LLM
    """
    # Filter logs based on options
    filtered_logs = []
    for log in thread_logs:
        # Skip usage events unless requested
        if log.role == "usage" and not include_usage:
            continue
            
        # Skip system events unless requested  
        if log.role == "system" and not include_system_events:
            continue
            
        filtered_logs.append(log)
    
    return reconstruct_chat_history_from_thread_logs(filtered_logs)


# NOT USED YET
def get_last_n_turns(thread_logs: List[ThreadLog], n_turns: int = 5) -> List[Dict[str, Any]]:
    """
    Get the last N conversation turns from thread logs.
    
    Args:
        thread_logs: List of ThreadLog objects from the database
        n_turns: Number of turns to include (user message + assistant response = 1 turn)
        
    Returns:
        List of chat messages for the last N turns
    """
    # Find TurnEnd events to identify turn boundaries
    turn_boundaries = []
    for i, log in enumerate(thread_logs):
        if log.event_name == "TurnEnd":
            turn_boundaries.append(i)
    
    if not turn_boundaries:
        # No turns found, return all
        return reconstruct_chat_history_from_thread_logs(thread_logs)
    
    # Get the last n_turns boundaries
    last_turns = turn_boundaries[-n_turns:] if len(turn_boundaries) >= n_turns else turn_boundaries
    
    if not last_turns:
        return []
    
    # Find the start index for the first turn we want to include
    start_idx = 0
    if len(last_turns) > 0:
        # Look for the previous TurnEnd or start of logs
        first_turn_end = last_turns[0]
        # Find the PromptStarted that begins this turn
        for i in range(first_turn_end, -1, -1):
            if thread_logs[i].event_name == "PromptStarted":
                start_idx = i
                break
    
    # Get logs from start_idx to end
    relevant_logs = thread_logs[start_idx:]
    
    return reconstruct_chat_history_from_thread_logs(relevant_logs)


# Use this for testing
def validate_chat_history(history: List[Dict[str, Any]]) -> List[Dict]:
    """
    Validate reconstructed chat history and return validation errors.
    
    Args:
        history: Chat history to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    seen_tool_id_results = set()

    for i, msg in enumerate(history):
        if not isinstance(msg, dict):
            errors.append(f"Message {i} is not a dictionary: {type(msg)}")
            continue
            
        if "role" not in msg:
            errors.append(f"Message {i} missing 'role' field")
            continue
            
        role = msg["role"]
        
        if role == "user":
            if "content" not in msg:
                errors.append(f"User message {i} missing 'content' field")
        elif role == "assistant":
            has_content = "content" in msg and msg["content"]
            has_tool_calls = "tool_calls" in msg and msg["tool_calls"]
            if not (has_content or has_tool_calls):
                errors.append(f"Assistant message {i} missing both 'content' and 'tool_calls'")
        elif role == "tool":
            required = ["tool_call_id", "content"]
            for field in required:
                if field not in msg:
                    errors.append(f"Tool message {i} missing '{field}' field")
            seen_tool_id_results.add(msg["tool_call_id"])
        else:
            errors.append(f"Message {i} has invalid role: {role}")
    
    # Strip any tool_calls that don't have a response since the AI will complain
    for i, msg in enumerate(history):
        if msg.get("role") == "assistant" and "tool_calls" in msg:
            tool_calls = [call for call in msg["tool_calls"] if call.get("id") in seen_tool_id_results]
            if len(tool_calls) > 0:
                msg["tool_calls"] = tool_calls
            else:
                del msg["tool_calls"]

    if len(errors) > 0:
        raise RuntimeError("Validation errors found in chat history: " + ", ".join(errors))

    return history

