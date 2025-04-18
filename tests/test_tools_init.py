import os
import importlib
import sys
import pytest
import inspect
from .utils.tools_utils import (
    find_tools_directory,
    get_base_tool_class,
    get_tool_classes_from_module,
    get_tool_files_in_directory
)

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

    tools_module = importlib.import_module('agentic.tools')
    all_list = getattr(tools_module, '__all__', [])
    
    tool_mapping = getattr(tools_module, '_TOOL_MAPPING', {})    
    tool_files = get_tool_files_in_directory(tools_dir)
    
    # Check each tool file
    missing_in_mapping = []
    missing_in_all = []
    
    for tool_file in tool_files:
        # Try to import the module to get its classes
        try:
            module_name = tool_file.removesuffix(".py")
            tool_classes = get_tool_classes_from_module(module_name)
            
            # Check if all tool classes are in the mapping and __all__
            for cls_name in tool_classes:
                # Check if in mapping
                if cls_name not in tool_mapping or tool_mapping[cls_name] != module_name:
                    missing_in_mapping.append(f"{cls_name} -> {module_name}")
                
                # Check if in __all__
                if cls_name not in all_list:
                    missing_in_all.append(cls_name)

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

def test_type_stub_matches_init():
    """
    Test that the __init__.pyi type stub file correctly includes all the tool classes
    that are in __all__ and _TOOL_MAPPING.
    """
    # Get the tools directory path
    try:
        tools_dir = find_tools_directory()
    except FileNotFoundError as e:
        pytest.skip(f"Skipping test: {str(e)}")
    
    # Path to the type stub file
    pyi_path = tools_dir / "__init__.pyi"
    
    # Check if the type stub file exists
    if not pyi_path.exists():
        pytest.skip("__init__.pyi does not exist")
    
    # Import the tools module to get __all__ and _TOOL_MAPPING
    if str(tools_dir.parent) not in sys.path:
        sys.path.insert(0, str(tools_dir.parent))
    
    tools_module = importlib.import_module('agentic.tools')
    all_list = getattr(tools_module, '__all__', [])
    tool_mapping = getattr(tools_module, '_TOOL_MAPPING', {})
    
    # Read the content of the type stub file
    with open(pyi_path, 'r') as f:
        pyi_content = f.read()
    
    # Check if all tool classes from __all__ are imported in the type stub
    missing_imports = []
    for tool_name in all_list:
        import_pattern = f"from .{tool_mapping.get(tool_name, '')} import {tool_name}"
        if import_pattern not in pyi_content:
            missing_imports.append(f"{tool_name} from {tool_mapping.get(tool_name, '')}")
    
    # Check if all tool classes are included in the __all__ list in the type stub
    missing_in_all = []
    
    # This regex pattern matches the __all__ list in the type stub file
    import re
    all_pattern = r"__all__\s*=\s*\[(.*?)\]"
    all_match = re.search(all_pattern, pyi_content, re.DOTALL)
    
    if all_match:
        pyi_all_content = all_match.group(1)
        for tool_name in all_list:
            if f'"{tool_name}"' not in pyi_all_content:
                missing_in_all.append(tool_name)
    else:
        missing_in_all = all_list  # All are missing if the __all__ list isn't found
    
    # Generate failure messages
    failure_msgs = []
    
    if missing_imports:
        failure_msgs.append(f"The following tool classes are missing from imports in __init__.pyi: {', '.join(missing_imports)}")
    
    if missing_in_all:
        failure_msgs.append(f"The following tool classes are missing from __all__ in __init__.pyi: {', '.join(missing_in_all)}")
    
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

    BaseAgenticTool = get_base_tool_class()
    tool_files = get_tool_files_in_directory(tools_dir, exclude_files=['__init__.py', 'base.py'])
    
    # Tool classes that don't inherit from BaseAgenticTool
    non_compliant_tools = []
    
    for tool_file in tool_files:            
        # Try to import the module to get its classes
        try:
            module_name = tool_file.removesuffix(".py")
            tool_classes = get_tool_classes_from_module(module_name)
            
            # Check inheritance
            for cls_name, cls in tool_classes.items():
                if not issubclass(cls, BaseAgenticTool):
                    non_compliant_tools.append(f"{module_name}.{cls_name}")
                    
        except (ImportError, AttributeError) as e:
            print(f"Warning: Could not inspect module {module_name}: {e}")
    
    # Fail the test if any tools don't inherit from BaseAgenticTool
    assert not non_compliant_tools, f"The following tool classes don't inherit from BaseAgenticTool: {', '.join(non_compliant_tools)}"

def test_all_tools_have_init_function():
    """
    Test that ensures all tool classes have a __init__ method.
    """
    # Get the tools directory path
    try:
        tools_dir = find_tools_directory()
    except FileNotFoundError as e:
        pytest.skip(f"Skipping test: {str(e)}")

    BaseAgenticTool = get_base_tool_class()
    base_init_function = BaseAgenticTool.__init__
    tool_files = get_tool_files_in_directory(tools_dir, exclude_files=['__init__.py', 'base.py'])
    
    # Tool classes that don't have a __init__ method
    missing_init = []
    non_callable_init = []
    non_overridden_init = []
    
    for tool_file in tool_files:            
        # Try to import the module to get its classes
        try:
            module_name = tool_file.removesuffix(".py")
            tool_classes = get_tool_classes_from_module(module_name)
            
            # Check for __init__ method
            for cls_name, cls in tool_classes.items():
                # Check if __init__ exists
                if not hasattr(cls, '__init__'):
                    missing_init.append(f"{module_name}.{cls_name}")
                    continue                
                
                # Check if __init__ is callable
                init_attr = getattr(cls, '__init__')
                if not callable(init_attr):
                    non_callable_init.append(f"{module_name}.{cls_name}")
                    continue

                # Check if get_tools has different signature than BaseAgenticTool
                init_function = cls.__dict__.get('__init__')
                print(f"get_tools_function: {init_function}\nBaseAgenticTool.__init__: {base_init_function}")
                
                if init_function is None or init_function is base_init_function:
                    non_overridden_init.append(f"{module_name}.{cls_name}")
                    continue
                    
        except (ImportError, AttributeError) as e:
            print(f"Warning: Could not inspect module {module_name}: {e}")
    
    # Build error messages
    errors = []
    
    if missing_init:
        errors.append(f"The following tool classes are missing the __init__ method: {', '.join(missing_init)}")
    
    if non_callable_init:
        errors.append(f"The following tool classes have a __init__ attribute that is not callable: {', '.join(non_callable_init)}")

    if non_overridden_init:
        errors.append(f"The following tool classes have a __init__ method that doesn't override the BaseAgenticTool's __init__ method: {', '.join(non_overridden_init)}")
    
    # Fail the test if any errors
    assert not errors, '\n'.join(errors)

def test_all_tools_have_get_tools_function():
    """
    Test that ensures all tool classes have a get_tools method.
    """
    # Get the tools directory path
    try:
        tools_dir = find_tools_directory()
    except FileNotFoundError as e:
        pytest.skip(f"Skipping test: {str(e)}")
    
    BaseAgenticTool = get_base_tool_class()
    base_get_tools = BaseAgenticTool.get_tools
    tool_files = get_tool_files_in_directory(tools_dir, exclude_files=['__init__.py', 'base.py'])
    
    # Tool classes that don't have a get_tools method
    missing_get_tools = []
    non_callable_get_tools = []
    non_overridden_get_tools = []
    
    for tool_file in tool_files:            
        # Try to import the module to get its classes
        try:
            module_name = tool_file.removesuffix(".py")
            tool_classes = get_tool_classes_from_module(module_name)
            
            # Check for get_tools method
            for cls_name, cls in tool_classes.items():
                # Check if get_tools exists
                if not hasattr(cls, 'get_tools'):
                    missing_get_tools.append(f"{module_name}.{cls_name}")
                    continue

                # Check if get_tools is callable
                get_tools_attr = getattr(cls, 'get_tools')
                if not callable(get_tools_attr):
                    non_callable_get_tools.append(f"{module_name}.{cls_name}")
                    continue

                # Check if get_tools has different signature than BaseAgenticTool
                get_tools_function = cls.__dict__.get('get_tools')
                if get_tools_function is None or get_tools_function is base_get_tools:
                    non_overridden_get_tools.append(f"{module_name}.{cls_name}")
                    
        except (ImportError, AttributeError) as e:
            print(f"Warning: Could not inspect module {module_name}: {e}")
    
    # Build error messages
    errors = []
    
    if missing_get_tools:
        errors.append(f"The following tool classes are missing the get_tools method: {', '.join(missing_get_tools)}")
    
    if non_callable_get_tools:
        errors.append(f"The following tool classes have a get_tools attribute that is not callable: {', '.join(non_callable_get_tools)}")
    
    if non_overridden_get_tools:
            errors.append(f"The following tool classes have a get_tools method that doesn't override the BaseAgenticTool's get_tools method: {', '.join(non_overridden_get_tools)}")

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
