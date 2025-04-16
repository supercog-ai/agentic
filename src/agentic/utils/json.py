from litellm.types.utils import Message
from pydantic import BaseModel
from datetime import datetime

def get_tc_args(tc):
    if isinstance(tc, dict):
        return make_json_serializable(tc)
    else:
        return make_json_serializable(tc.function.arguments)
    
def get_tc_name(tc):
    if isinstance(tc, dict):
        print("TC: ", tc)
        return str(tc)
    else:
        return tc.function.name
                
def make_json_serializable(obj):
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
                    "id": tc.id,
                    "type": tc.type
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
