import os
import importlib
import inspect
import sys
import pytest
from .utils.tools_utils import find_tools_directory, get_tool_classes_from_module

def test_all_tools_are_registered():
    """
    Test that ensures all tool classes correctly register themselves with the tool registry.
    This test checks that:
    1. All classes ending with 'Tool' are registered in the tool registry
    2. The tool registry contains entries for all expected tool classes
    """
    # Get the tools directory path
    try:
        tools_dir = find_tools_directory()
    except FileNotFoundError as e:
        pytest.skip(f"Skipping test: {str(e)}")
    
    # Import the tools module to access its components
    if str(tools_dir.parent) not in sys.path:
        sys.path.insert(0, str(tools_dir.parent))
    
    # Get access to the tool registry
    try:
        registry_module = importlib.import_module('agentic.tools.utils.registry')
        tool_registry = getattr(registry_module, 'tool_registry')
    except (ImportError, AttributeError) as e:
        pytest.fail(f"Could not access tool registry: {e}")
    
    # Find all Python files in the tools directory (excluding __init__.py)
    tool_files = [f for f in os.listdir(tools_dir) 
                 if f.endswith('.py') and f != '__init__.py']
    
    # Find all tool classes
    unregistered_tools = []
    
    for tool_file in tool_files:            
        # Try to import the module to get its classes
        try:
            module_name = tool_file.removesuffix(".py")
            tool_classes = get_tool_classes_from_module(module_name)
            
            # Check registration status
            for cls in tool_classes:                
                # Check if the tool is registered or a parent class
                registered_tools = tool_registry.get_tools().keys()
                if cls not in registered_tools and cls not in ['OAuthTool', 'BaseAgenticTool']:
                    unregistered_tools.append(cls)
                    
        except (ImportError, AttributeError) as e:
            print(f"Warning: Could not inspect module {module_name}: {e}")
    
    # Fail the test if any tools are not registered
    if unregistered_tools:
        unregistered_tools.sort()
        pytest.fail(f"The following tool classes are not registered with the tool registry: {', '.join(unregistered_tools)}")

def test_tool_registry_functionality():
    """
    Test the functionality of the tool registry.
    This test verifies that:
    1. The tool registry can be accessed
    2. Tools can be correctly retrieved from the registry
    3. The registry contains the expected tools
    """
    # Import the registry module
    try:
        registry_module = importlib.import_module('agentic.tools.utils.registry')
        tool_registry = getattr(registry_module, 'tool_registry')
    except (ImportError, AttributeError) as e:
        pytest.fail(f"Could not access tool registry: {e}")
    
    # Test registry functionality on well-known tool
    try:
        weather_tool = tool_registry.get_tool("WeatherTool")
        assert weather_tool is not None, "WeatherTool should be registered"
        
        # Verify the tool has the expected attributes
        assert hasattr(weather_tool.function, 'get_tools'), "WeatherTool should have get_tools method"
    except Exception as e:
        pytest.fail(f"Failed to access WeatherTool from registry: {e}")
    
    # Check if the registry has a method to list all tools
    if hasattr(tool_registry, 'get_tools'):
        all_registered = tool_registry.get_tools()
        assert isinstance(all_registered, dict), "get_tools should return a dictionary"
        assert "WeatherTool" in all_registered, "WeatherTool should be in the tools dictionary"
