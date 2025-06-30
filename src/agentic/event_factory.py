from typing import Optional, Dict, Type

from agentic.db.models import ThreadLog
from agentic.events import (
    AddChild,
    ChatOutput,
    Event,
    FinishCompletion,
    OAuthFlow,
    Output,
    Prompt,
    PromptStarted,
    ReasoningContent,
    ResetHistory,
    ResumeWithInput,
    SetState,
    StartCompletion,
    ToolCall,
    ToolError,
    ToolResult,
    TurnCancelled,
    TurnEnd,
    WaitForInput,
)


class EventFactory:
    """Factory to reconstruct events from database records"""
    
    # Map event names to event classes
    EVENT_MAP: Dict[str, Type[Event]] = {
        "prompt": Prompt,
        "prompt_started": PromptStarted,
        "reset_history": ResetHistory,
        "chat_output": ChatOutput,
        "output": Output,
        "tool_call": ToolCall,
        "tool_result": ToolResult,
        "tool_error": ToolError,
        "completion_start": StartCompletion,
        "completion_end": FinishCompletion,
        "turn_end": TurnEnd,
        "turn_cancelled": TurnCancelled,
        "set_state": SetState,
        "add_child": AddChild,
        "wait_for_input": WaitForInput,
        "resume_with_input": ResumeWithInput,
        "oauth_flow": OAuthFlow,
        "reasoning_content": ReasoningContent,
    }
    
    @classmethod
    def from_thread_log(cls, log: ThreadLog) -> Optional[Event]:
        """Reconstruct an event from a ThreadLog entry"""
        event_name = log.event_name
        
        try:
            # Get the appropriate event class
            event_class = cls.EVENT_MAP.get(event_name)
            
            if event_class and hasattr(event_class, 'from_thread_log'):
                # Use the class's from_thread_log method
                return event_class.from_thread_log(log)
            else:
                # Fallback for unknown event types or classes without from_thread_log
                return Event(
                    agent=log.agent_id,
                    type=event_name,
                    payload=log.event,
                    depth=log.depth,
                )
                
        except Exception as e:
            print(f"Error reconstructing event {event_name} from log {log.id}: {e}")
            # Return a generic event with the raw data
            return Event(
                agent=log.agent_id,
                type=event_name,
                payload=log.event,
                depth=0
            )
