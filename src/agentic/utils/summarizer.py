import litellm
from litellm import completion
from agentic.llm import setup_model_key

def generate_document_summary(text: str, mime_type: str, model: str = "openai/gpt-4o") -> str:
    """Generate a concise document summary using LLM"""
    try:
        setup_model_key(model)
        
        # Get model context window from LiteLLM's model list
        model_info = litellm.get_model_info(model)
        context_window = model_info.get("max_input_tokens", 128000)
        max_output_tokens = model_info.get("max_output_tokens", 4096)
        
        system_message = f"Generate a 3-sentence summary of this {mime_type} document."
        system_tokens = litellm.token_counter(
            model=model, 
            text=system_message,
            count_response_tokens=True
        )
        
        max_input_tokens = min(
            int(context_window * 0.8) - system_tokens,
            context_window - max_output_tokens - system_tokens
        )
        
        if max_input_tokens <= 0:
            return "Error: Context window too small for summary generation"

        truncated_text = _truncate_for_model(
            text=text,
            model=model,
            max_tokens=max_input_tokens
        )

        # Ensure max_tokens doesn't exceed model's output limit
        safe_max_tokens = min(int(context_window * 0.2), max_output_tokens)
        
        response = completion(
            model=model,
            messages=[{
                "role": "system",
                "content": system_message
            }, {
                "role": "user", 
                "content": truncated_text
            }],
            max_tokens=safe_max_tokens
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Summary generation failed: {str(e)}"


def _truncate_for_model(text: str, model: str, max_tokens: int) -> str:
    """Reuse the project's standard text truncation logic"""
    try:
        tokens = litellm.encode(model=model, text=text)
        return litellm.decode(model=model, tokens=tokens[:max_tokens])
    except:
        return text[:int(max_tokens*4)]

def summarize_chat_history(messages: list, model: str, max_tokens: int = None) -> str:
    """Summarize conversation history with token limit control"""
    try:
        # Filter out any messages with None or missing content
        non_empty_messages = []
        for m in messages:
            if "content" in m and m["content"] is not None and m["content"].strip():
                non_empty_messages.append(m)
            elif "tool_calls" in m and m["tool_calls"]:
                # Create a representation of tool calls
                tool_call_content = []
                for tc in m["tool_calls"]:
                    if "function" in tc:
                        func_name = tc["function"].get("name", "unknown")
                        args = tc["function"].get("arguments", "{}")
                        tool_call_content.append(f"Called tool: {func_name} with arguments: {args}")
                
                if tool_call_content:
                    non_empty_messages.append({
                        "role": m["role"],
                        "content": " | ".join(tool_call_content)
                    })
        
        if not non_empty_messages:
            return "No prior conversation history."
            
        chat_content = "\n".join(
            f"{m['role']}: {m['content']}" 
            for m in non_empty_messages
        )
        
        # Choose a summarization model from the same provider
        summary_model = model

        
        model_info = litellm.get_model_info(summary_model)
        context_window = model_info.get("max_input_tokens", 128000)
        
        # Use provided max_tokens or default to 25% of context window
        summary_tokens = max_tokens or int(context_window * 0.25)
        
        truncated = _truncate_for_model(
            text=chat_content,
            model=summary_model,
            max_tokens=summary_tokens
        )
        
        response = completion(
            model=summary_model,
            messages=[{
                "role": "system",
                "content": "Condense this conversation history into a concise summary preserving key facts, decisions, and context."
            }, {
                "role": "user",
                "content": truncated
            }],
            max_tokens=summary_tokens
        )
        
        summary = response.choices[0].message.content
        return summary if summary.strip() else "Previous conversation contained relevant context."
        
    except Exception as e:
        return f"Previous conversation contained relevant context. (Summarization error: {str(e)})"