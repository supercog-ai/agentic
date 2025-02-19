def make_json_serializable(obj):
    """Recursively convert dictionary values to JSON-serializable types."""
    if isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif hasattr(obj, '__dict__'):  # For objects like RunContext
        return str(obj)
    return obj
