import json
from typing import Optional, Dict, Callable, Any, List
from uuid import uuid4
from litellm import Message
import traceback
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
from agentic.db.models import ThreadLog
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
        self.db_manager = DatabaseManager(db_path=self.db_path)
    
    def handle_event(self, event: Event, thread_context: ThreadContext) -> None:
        """Generic event handler that processes all events and logs them appropriately"""
        # Initialize a new thread when we see a Prompt event

        if isinstance(event, PromptStarted):
            if type(event.payload)==dict:
                prompt = event.payload['content']
            else:
                prompt = str(event.payload)

            # Check if the thread is in the database
            thread = self.db_manager.get_thread(thread_id=self.initial_thread_id)
            if not thread:
                thread = self.db_manager.create_thread(
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
            
        try:
            # Log the event
            self.db_manager.log_event(
                thread_id=thread_context.thread_id,
                agent_id=thread_context.agent_name,
                user_id=str(thread_context.get("user") or "default"),
                role=role,
                event_name=event_name,
                event_data=make_json_serializable(event_data)
            )
        except Exception as e:
            traceback.print_exc()
            print(f"Error logging event {event_name} for thread {thread_context.thread_id}: {e}. Data: {event_data}")

        # Reset usage tracking after a turn ends
        if isinstance(event, TurnEnd):
            self.usage_data = {}

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
    current_tool_calls = []
    tool_call_counter = 0
    
    for log in thread_logs:
        event_name = log.event_name
        event_data = log.event
        role = log.role
        
        # Handle user messages from PromptStarted events
        if event_name == "prompt_started":
            content = ""
            if isinstance(event_data, dict):
                content = event_data.get("content", "")
            elif isinstance(event_data, str):
                content = event_data
            
            if content:
                history.append({
                    "role": "user",
                    "content": content
                })
        
        # Handle assistant streaming responses from Output events  
        elif event_name == "chat_output" and role in ["assistant", "system"]:
            if current_assistant_message is None:
                current_assistant_message = {
                    "role": "assistant",
                    "content": ""
                }
            
            # Extract content from event_data
            content = ""
            if isinstance(event_data, dict):
                content = event_data.get("content", "")
            elif isinstance(event_data, str):
                content = event_data
                
            if content:
                current_assistant_message["content"] += content
        
        # Handle tool calls
        elif event_name == "tool_call":
            tool_call_counter += 1
            tool_call = {
                "id": f"call_{tool_call_counter}",
                "type": "function",
                "function": {
                    "name": event_data.get("name", ""),
                    "arguments": json.dumps(event_data.get("arguments", {})) if isinstance(event_data, dict) else "{}"
                }
            }
            current_tool_calls.append(tool_call)
            history.append({
                "role": "assistant",
                "content": "null",
                "tool_calls": [tool_call]
            })
        
        # Handle tool results
        elif event_name == "tool_result":
            if isinstance(event_data, dict):
                if event_data.get("is_log") == True:
                    # Skip log messages
                    continue
            # Find the corresponding tool call
            tool_name = event_data.get("name", "")
            result = event_data.get("result", "")
            
            # Find matching tool call ID
            call_id = None
            for tool_call in current_tool_calls:
                if tool_call["function"]["name"] == tool_name:
                    call_id = tool_call["id"]
                    break
            
            if call_id is None:
                continue  # Skip if no matching tool call found
            
            history.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": str(result)
            })
        
        # Handle tool errors (similar to tool results)
        elif event_name == "tool_error":
            tool_name = event_data.get("tool_name", "") if isinstance(event_data, dict) else ""
            error_msg = event_data.get("error", "") if isinstance(event_data, dict) else str(event_data)
            
            # Find matching tool call ID
            call_id = None
            for tool_call in current_tool_calls:
                if tool_call["function"]["name"] == tool_name:
                    call_id = tool_call["id"]
                    break
            
            if call_id is None:
                call_id = f"call_{tool_name}_{tool_call_counter}"
            
            history.append({
                "role": "tool", 
                "tool_call_id": call_id,
                "content": f"Error: {error_msg}"
            })
        
        # Handle completion finish - finalize assistant message
        elif event_name == "completion_end":
            if current_assistant_message is not None or current_tool_calls:
                assistant_msg = current_assistant_message or {"role": "assistant", "content": ""}
                
                # Add tool calls if any were made
                #if current_tool_calls:
                #    assistant_msg["tool_calls"] = current_tool_calls.copy()
                
                # Only add if there's content or tool calls
                if assistant_msg.get("content") or assistant_msg.get("tool_calls"):
                    history.append(assistant_msg)
                
                # Reset for next message
                current_assistant_message = None
                current_tool_calls = []
        
        # Handle turn end - ensure any pending assistant message is added
        elif event_name == "turn_end":
            if current_assistant_message is not None:
                history.append(current_assistant_message)
                current_assistant_message = None
            
            # Reset tool calls for next turn
            current_tool_calls = []
    
    # Handle any remaining assistant message at the end
    if current_assistant_message is not None:
        history.append(current_assistant_message)
    
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

