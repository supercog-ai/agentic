from litellm.types.utils import Message, ChatCompletionMessageToolCall
from pydantic import BaseModel
from datetime import datetime
import traceback

def get_tc_args(tc):
    if isinstance(tc, dict):
        return make_json_serializable(tc)
    else:
        return make_json_serializable(tc.function.arguments)
    
def get_tc_name(tc):
    if isinstance(tc, dict):
        return str(tc)
    else:
        return tc.function.name

def get_obj_value(obj, key):
    """Get the value of a key in an object, handling nested dictionaries."""
    if isinstance(obj, dict):
        return obj.get(key)
    elif hasattr(obj, '__dict__'):
        return getattr(obj, key, None)
    return None
                
def make_json_serializable(obj):
    try:
        """Recursively convert dictionary values to JSON-serializable types."""
        if isinstance(obj, dict):
            return {key: make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [make_json_serializable(item) for item in obj]
        elif isinstance(obj, Message):
            # Convert Message object to a dictionary manually
            return {
                "role": obj.role,
                "content": make_json_serializable(obj.content),
                "tool_calls": [
                    {
                        "function": {
                            "arguments": get_tc_args(tc),
                            "name": get_tc_name(tc)
                        },
                        "id": get_obj_value(tc, 'id'),
                        "type": get_obj_value(tc, 'type')
                    } for tc in (obj.tool_calls or [])
                ] if obj.tool_calls else None,
                "function_call": make_json_serializable(obj.function_call)
            }
        elif isinstance(obj, BaseModel):
            return obj.model_dump()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # For objects like RunContext
            return str(obj)
        return obj
    except Exception as e:
        traceback.print_exc()
        return str(obj)
