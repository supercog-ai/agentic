import inspect
import importlib
from pathlib import Path
from typing import Any

def find_tools_directory():
    """
    Find the tools directory by searching up from the current directory.
    Returns the Path object for the tools directory if found.
    """
    # Start with the current working directory
    current_dir = Path.cwd()
    
    # Try to find the tools directory by walking up the directory tree
    while current_dir != current_dir.parent:  # Stop at the root directory
        # Check if 'agentic/tools' exists in this directory
        tools_path = current_dir / 'src' / 'agentic' / 'tools'
        if tools_path.exists() and tools_path.is_dir():
            return tools_path
        
        # Also check for direct 'agentic/tools' pattern
        alt_path = current_dir / 'agentic' / 'tools'
        if alt_path.exists() and alt_path.is_dir():
            return alt_path
            
        # Move up one directory
        current_dir = current_dir.parent
    
    # If we couldn't find it, one last attempt by using the module info
    try:
        import agentic.tools
        return Path(inspect.getfile(agentic.tools)).parent
    except (ImportError, TypeError):
        pass
        
    raise FileNotFoundError("Could not find the tools directory in any parent directory")

def get_tool_classes_from_module(module_name: str) -> dict[str, type[Any]]:
    module = importlib.import_module(f'agentic.tools.{module_name}')
    
    # Find tool classes in the module
    tool_classes = {}
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and name.__contains__('Tool') and obj.__module__ == f'agentic.tools.{module_name}':
            tool_classes[name] = obj

    return tool_classes