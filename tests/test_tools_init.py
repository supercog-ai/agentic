import os
import importlib
import sys
import pytest
from .utils.tools_utils import find_tools_directory, get_tool_classes_from_module

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
        # Try to import the module to get its classes
        try:
            module_name = tool_file.removesuffix(".py")
            tool_classes = get_tool_classes_from_module(module_name)
            
            # Check if all tool classes are in the mapping and __all__
            for cls in tool_classes:
                # Check if in mapping
                if cls not in tool_mapping or tool_mapping[cls] != module_name:
                    missing_in_mapping.append(f"{cls} -> {module_name}")
                
                # Check if in __all__
                if cls not in all_list:
                    missing_in_all.append(cls)

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
        # Try to import the module to get its classes
        try:
            module_name = tool_file.removesuffix(".py")
            tool_classes = get_tool_classes_from_module(module_name)
            
            # Check inheritance
            for cls in tool_classes:
                if not issubclass(tool_classes[cls], BaseAgenticTool):
                    non_compliant_tools.append(f"{module_name}.{cls}")
                    
        except (ImportError, AttributeError) as e:
            print(f"Warning: Could not inspect module {module_name}: {e}")
    
    # Fail the test if any tools don't inherit from BaseAgenticTool
    assert not non_compliant_tools, f"The following tool classes don't inherit from BaseAgenticTool: {', '.join(non_compliant_tools)}"

def test_all_tools_have_get_tools_function():
    """
    Test that ensures all tool classes have a get_tools method.
    """
    # Get the tools directory path
    try:
        tools_dir = find_tools_directory()
    except FileNotFoundError as e:
        pytest.skip(f"Skipping test: {str(e)}")
    
    # Import the tools module
    if str(tools_dir.parent) not in sys.path:
        sys.path.insert(0, str(tools_dir.parent))
    
    # Find all Python files in the tools directory (excluding __init__.py)
    tool_files = [f for f in os.listdir(tools_dir) 
                 if f.endswith('.py') and f != '__init__.py']
    
    # Tool classes that don't have a get_tools method
    missing_get_tools = []
    non_callable_get_tools = []
    empty_get_tools = []
    
    for tool_file in tool_files:            
        # Try to import the module to get its classes
        try:
            module_name = tool_file.removesuffix(".py")
            tool_classes = get_tool_classes_from_module(module_name)
            
            # Check for get_tools method
            for cls in tool_classes:
                # Check if get_tools exists
                if not hasattr(tool_classes[cls], 'get_tools'):
                    missing_get_tools.append(f"{module_name}.{cls}")
                    continue
                
                # Check if get_tools is callable
                get_tools_attr = getattr(tool_classes[cls], 'get_tools')
                if not callable(get_tools_attr):
                    non_callable_get_tools.append(f"{module_name}.{cls}")
                    continue
                    
        except (ImportError, AttributeError) as e:
            print(f"Warning: Could not inspect module {module_name}: {e}")
    
    # Build error messages
    errors = []
    
    if missing_get_tools:
        errors.append(f"The following tool classes are missing the get_tools method: {', '.join(missing_get_tools)}")
    
    if non_callable_get_tools:
        errors.append(f"The following tool classes have a get_tools attribute that is not callable: {', '.join(non_callable_get_tools)}")
    
    if empty_get_tools:
        # This is a warning, not an error
        print(f"Warning: The following tool classes have get_tools methods that return empty lists: {', '.join(empty_get_tools)}")
    
    # Fail the test if any errors
    assert not errors, '\n'.join(errors)

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
