import inspect
import importlib
import os
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

def get_base_tool_class():
    """
    Get the BaseAgenticTool class from the base module.
    """
    try:
        base_module = importlib.import_module('agentic.tools.base')
        return getattr(base_module, 'BaseAgenticTool')
    except (ImportError, AttributeError) as e:
        raise ImportError("Could not import BaseAgenticTool: " + str(e))

def get_tool_files_in_directory(directory: Path | str, exclude_files: list[Path | str] = ['__init__.py']) -> list[Path]:
    """
    Get a list of all Python files in the given directory excluding the specified files.
    """
    return [
        f for f in os.listdir(directory) 
        if f.endswith('.py') and f not in exclude_files
    ]
