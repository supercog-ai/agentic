from litellm.types.utils import Message
from datetime import datetime

def make_json_serializable(obj):
    """Recursively convert dictionary values to JSON-serializable types."""
    if isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, Message):
        # Convert Message object to a dictionary manually
        return {
            "content": obj.content,
            "role": obj.role,
            "tool_calls": [
                {
                    "function": {
                        "arguments": tc.function.arguments,
                        "name": tc.function.name
                    },
                    "id": tc.id,
                    "type": tc.type
                } for tc in (obj.tool_calls or [])
            ] if obj.tool_calls else None,
            "function_call": obj.function_call
        }
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):  # For objects like RunContext
        return str(obj)
    return obj
