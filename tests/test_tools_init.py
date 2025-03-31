import os
import importlib
import inspect
import sys
import pytest
from pathlib import Path

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

def test_all_tools_are_imported_and_listed():
    """
    Test that ensures all tool modules in the tools directory are:
    1. Properly mapped in the _TOOL_MAPPING dictionary in __init__.py
    2. Their tool classes are listed in the __all__ variable
    
    This test is compatible with the lazy-loading implementation.
    """
    # Get the tools directory path
    try:
        tools_dir = find_tools_directory()
    except FileNotFoundError as e:
        pytest.skip(f"Skipping test: {str(e)}")
    
    # Import the tools module to inspect its __all__ variable
    if str(tools_dir.parent) not in sys.path:
        sys.path.insert(0, str(tools_dir.parent))
    
    tools_module = importlib.import_module('agentic.tools')
    all_list = getattr(tools_module, '__all__', [])
    
    # Get the tool mapping dictionary
    tool_mapping = getattr(tools_module, '_TOOL_MAPPING', {})
    
    # Find all Python files in the tools directory (excluding __init__.py)
    tool_files = [f for f in os.listdir(tools_dir) 
                 if f.endswith('.py') and f != '__init__.py']
    
    # Check each tool file
    missing_in_mapping = []
    missing_in_all = []
    
    for tool_file in tool_files:
        module_name = tool_file[:-3]  # Remove .py extension
            
        # Try to import the module to get its classes
        try:
            module = importlib.import_module(f'agentic.tools.{module_name}')
            
            # Find tool classes in the module
            # Assuming tool classes end with 'Tool' by convention
            tool_classes = [name for name, obj in inspect.getmembers(module)
                           if inspect.isclass(obj) and name.endswith('Tool') 
                           and obj.__module__ == f'agentic.tools.{module_name}']
            
            # Check if all tool classes are in the mapping and __all__
            for class_name in tool_classes:
                # Check if in mapping
                if class_name not in tool_mapping or tool_mapping[class_name] != module_name:
                    missing_in_mapping.append(f"{class_name} -> {module_name}")
                
                # Check if in __all__
                if class_name not in all_list:
                    missing_in_all.append(class_name)
                    
        except (ImportError, AttributeError) as e:
            print(f"Warning: Could not inspect module {module_name}: {e}")
    
    # Generate failure messages
    failure_msgs = []
    
    if missing_in_mapping:
        failure_msgs.append(f"The following tool classes are missing or incorrectly mapped in _TOOL_MAPPING: {', '.join(missing_in_mapping)}")
    
    if missing_in_all:
        failure_msgs.append(f"The following tool classes are not listed in __all__: {', '.join(missing_in_all)}")
    
    # Fail the test if any issues found
    assert not failure_msgs, '\n'.join(failure_msgs)


def test_tools_inherit_from_base_class():
    """
    Test that ensures all tool classes inherit from BaseAgenticTool.
    Compatible with lazy-loading implementation.
    """
    # Get the tools directory path
    try:
        tools_dir = find_tools_directory()
    except FileNotFoundError as e:
        pytest.skip(f"Skipping test: {str(e)}")
    
    # Import the tools module
    if str(tools_dir.parent) not in sys.path:
        sys.path.insert(0, str(tools_dir.parent))
    
    # Import the base tool class directly from the module to avoid lazy loading issues
    try:
        base_module = importlib.import_module('agentic.tools.base')
        BaseAgenticTool = getattr(base_module, 'BaseAgenticTool')
    except (ImportError, AttributeError) as e:
        pytest.fail(f"Could not import BaseAgenticTool: {e}")
    
    # Find all Python files in the tools directory (excluding __init__.py)
    tool_files = [f for f in os.listdir(tools_dir) 
                 if f.endswith('.py') and f != '__init__.py' and f != 'base.py']
    
    # Tool classes that don't inherit from BaseAgenticTool
    non_compliant_tools = []
    
    for tool_file in tool_files:
        module_name = tool_file[:-3]  # Remove .py extension
            
        # Try to import the module to get its classes
        try:
            module = importlib.import_module(f'agentic.tools.{module_name}')
            
            # Find tool classes in the module
            tool_classes = [
                (name, obj) for name, obj in inspect.getmembers(module)
                if (inspect.isclass(obj) and 
                    name.endswith('Tool') and 
                    obj.__module__ == f'agentic.tools.{module_name}')
            ]
            
            # Check inheritance
            for class_name, cls in tool_classes:
                if not issubclass(cls, BaseAgenticTool):
                    non_compliant_tools.append(f"{module_name}.{class_name}")
                    
        except (ImportError, AttributeError) as e:
            print(f"Warning: Could not inspect module {module_name}: {e}")
    
    # Fail the test if any tools don't inherit from BaseAgenticTool
    assert not non_compliant_tools, f"The following tool classes don't inherit from BaseAgenticTool: {', '.join(non_compliant_tools)}"


def test_lazy_loading_works():
    """
    Test that the lazy loading mechanism works as expected.
    Attempts to load each tool class via the lazy loading mechanism.
    """
    # Import the tools module
    tools_module = importlib.import_module('agentic.tools')
    all_list = getattr(tools_module, '__all__', [])
    
    # Try to access each tool class
    failed_imports = []
    
    for tool_name in all_list:
        try:
            # This should trigger the __getattr__ method
            tool_class = getattr(tools_module, tool_name)
        except (AttributeError, ImportError) as e:
            failed_imports.append(f"{tool_name}: {str(e)}")
    
    # Fail the test if any imports failed
    assert not failed_imports, f"The following tool classes failed to lazy load: {', '.join(failed_imports)}"
