import litellm
from typing import List, Dict, Any, Tuple, Optional
import logging

def count_tokens_in_messages(messages: List[Dict[str, Any]], model: str) -> int:
    """
    Count tokens in a message array with robust fallbacks
    
    Args:
        messages: List of message objects
        model: Name of the model to count tokens for
        
    Returns:
        int: Estimated token count
    """
    try:
        # First try the most accurate method - count entire messages array
        return litellm.token_counter(model=model, messages=messages)
    except Exception as e:
        # Fallback to individual message counting
        token_count = 0
        for m in messages:
            try:
                if "content" in m and m["content"] is not None:
                    token_count += litellm.token_counter(model=model, text=m["content"])
                elif "tool_calls" in m and m["tool_calls"]:
                    try:
                        # Try using the tools parameter directly
                        tool_tokens = litellm.token_counter(
                            model=model, 
                            tools=m["tool_calls"]
                        )
                        token_count += tool_tokens
                    except Exception as tool_exception:
                        # Fallback to string representation
                        for tool_call in m["tool_calls"]:
                            if "function" in tool_call:
                                func_text = f"{tool_call['function'].get('name', '')} {tool_call['function'].get('arguments', '{}')}"
                                token_count += litellm.token_counter(model=model, text=func_text)
                
                # Add overhead for message formatting
                token_count += 4
            except Exception:
                # Last resort: add a large safety buffer
                token_count += 500
                
        return token_count

def should_compress_context(
    messages: List[Dict[str, Any]], 
    model: str,
    safety_factor: float = 0.3
) -> Tuple[bool, int, int]:
    """
    Check if the current context should be compressed based on token count
    
    Args:
        messages: List of message objects
        model: Model name
        safety_factor: Percentage of context window to reserve (0.0-1.0)
        
    Returns:
        Tuple[bool, int, int]: (should_compress, current_tokens, max_allowed_tokens)
    """
    # Get model context window size
    model_info = litellm.get_model_info(model)
    context_window = model_info.get("max_input_tokens", 128000)
    
    # Calculate safety margin
    safety_margin = int(context_window * safety_factor)
    max_allowed_tokens = context_window - safety_margin
    
    # Count tokens in current messages
    current_tokens = count_tokens_in_messages(messages, model)
    
    # Determine if compression is needed
    return current_tokens > max_allowed_tokens, current_tokens, max_allowed_tokens
    
def create_compressed_messages(
    messages: List[Dict[str, Any]],
    model: str,
    current_tokens: Optional[int] = None,
    target_percentage: float = 0.6,
    debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Create a compressed version of message history using summarization
    
    Args:
        messages: List of message objects
        model: Model name for token counting
        current_tokens: Pre-calculated token count (optional)
        target_percentage: Target percentage of context window to use
        debug: Whether to print debug info
        
    Returns:
        List[Dict[str, Any]]: Compressed message list
    """
    from agentic.utils.summarizer import summarize_chat_history
    
    # Get model context window size
    model_info = litellm.get_model_info(model)
    context_window = model_info.get("max_input_tokens", 128000)
    
    # Calculate target token count
    target_token_count = int(context_window * target_percentage)
    
    # Make sure we have enough messages to summarize
    if len(messages) <= 4:
        if debug:
            print(f"[Compression] Not enough messages to summarize: {len(messages)}")
        return messages
    
    try:
        # Determine messages to summarize (exclude system and last 3 messages)
        messages_to_summarize = messages[1:-3]
        
        if not messages_to_summarize:
            if debug:
                print("[Compression] No messages to summarize")
            return messages
            
        # Get summary
        summary = summarize_chat_history(
            messages_to_summarize,
            model=model,
            max_tokens=int(target_token_count * 0.25)  # Limit summary to 25% of target
        )
        
        # Ensure summary isn't empty
        if not summary or summary.strip() == "":
            summary = "Previous conversation contained relevant context about the current task."
        
        # Build new message list with summary
        compressed_messages = [
            messages[0],  # System instructions
            {"role": "system", "content": f"Previous conversation summary: {summary}"}
        ]
        
        # Add recent messages, ensuring none are empty
        for msg in messages[-3:]:
            if msg.get("content") and msg["content"].strip():
                compressed_messages.append(msg)
            elif msg.get("tool_calls"):
                compressed_messages.append(msg)
        
        # Validate our new token count
        new_token_count = count_tokens_in_messages(compressed_messages, model)
        
        # If still too large, keep only 1 recent message
        if new_token_count > target_token_count:
            if debug:
                print(f"[Compression] Compressed message still too large: {new_token_count} > {target_token_count}")
            compressed_messages = [
                messages[0],
                {"role": "system", "content": f"Previous conversation summary: {summary}"},
                messages[-1]  # Only the most recent message
            ]
        
        if debug:
            print(f"[Compression] Reduced messages from {len(messages)} to {len(compressed_messages)}")
            
        return compressed_messages
        
    except Exception as e:
        # If summarization fails, take an aggressive approach
        logging.error(f"Summarization failed: {str(e)}")
        return [messages[0], messages[-1]] 