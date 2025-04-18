from dataclasses import dataclass
from typing import List, Callable, Optional, Dict, Any, Type, Union
import importlib
import inspect

import shutil
import subprocess
from contextlib import contextmanager

@dataclass
class Dependency:
    name: str
    type: str  # 'pip' or 'system'
    version: Optional[str] = None

@dataclass
class ConfigRequirement:
    key: str
    description: str
    required: bool = True
    default: Any = None


def check_package(package_name):
    try:
        # Method 1: Try importing the module directly
        __import__(package_name)
        return True
    except ImportError:
        # If direct import fails, we can try using pkg_resources
        try:
            import pkg_resources

            pkg_resources.require(package_name)
            return True
        except (ImportError, pkg_resources.DistributionNotFound):
            return False
        except pkg_resources.ContextualVersionConflict:
            return True


@dataclass
class Tool:
    name: str
    description: str
    function: Callable
    dependencies: List[Dependency]
    config_requirements: List[ConfigRequirement] = None

    def __post_init__(self):
        self.config_requirements = self.config_requirements or []

class ToolRegistry:
    Dependency = Dependency

    def __init__(self, auto_install: bool = False):
        self._tools: Dict[str, Tool] = {}  # Map of tool names to Tool objects
        self._class_tools: Dict[Type, str] = {}  # Map of class types to tool names
        self.auto_install = auto_install

    def register(
        self,
        name: str,
        description: str,
        dependencies: List[Dependency] = None,
        config_requirements: List[ConfigRequirement] = None,
    ):
        """Decorator to register a new tool with its dependencies."""

        def decorator(target):
            tool = Tool(
                name=name,
                description=description,
                function=target,
                dependencies=dependencies or [],
                config_requirements=config_requirements or [],
            )
            
            # Store by name for direct lookup
            self._tools[name] = tool
            
            # Also store class reference for when we need to look up by class
            if isinstance(target, type):
                self._class_tools[target] = name
                
            return target

        return decorator

    def get_tool(self, name_or_class: Union[str, Type]) -> Optional[Tool]:
        """
        Get a tool by name or class.
        
        Args:
            name_or_class: Either a string tool name or a class type
            
        Returns:
            The Tool object if found, or None if not found
        """
        if isinstance(name_or_class, str):
            # Direct lookup by name
            return self._tools.get(name_or_class)
        elif isinstance(name_or_class, type):
            # Lookup by class
            tool_name = self._class_tools.get(name_or_class)
            if tool_name:
                return self._tools.get(tool_name)
                
            # If not found directly, try to find by class hierarchy
            for cls in inspect.getmro(name_or_class):
                if cls in self._class_tools:
                    return self._tools.get(self._class_tools[cls])
                    
        return None

    def get_tools(self) -> Dict[str, Tool]:
        """
        Get all registered tools.
        
        Returns:
            Dictionary mapping tool names to Tool objects
        """
        return self._tools.copy()

    @contextmanager
    def safe_imports(self):
        """Context manager to safely handle import errors."""
        try:
            yield
        except ImportError as e:
            print(f"Import error: {e}")
        except ModuleNotFoundError as e:
            print(f"Module not found: {e}")
        except Exception as e:
            print(f"Unexpected error during import: {e}")

    def check_pip_dependency(self, dep: Dependency) -> bool:
        """Check if a Python package is installed."""
        try:
            importlib.import_module(dep.name)
            return True
        except ImportError:
            return False

    def is_package_installed(self, package_name):
        return check_package(package_name)

    def check_system_dependency(self, dep: Dependency) -> bool:
        """Check if a system binary is available."""
        return shutil.which(dep.name) is not None

    def install_pip_dependency(self, dep: Dependency) -> bool:
        """Install a Python package using pip."""
        try:
            if dep.version and dep.version.startswith("https://"):
                subprocess.check_call(["uv", "pip", "install", dep.version])
            else:
                if dep.version and dep.version.startswith("^"):
                    version_spec = f"{dep.name}>={dep.version[1:]}"
                else:
                    version_spec = dep.name
                subprocess.check_call(["uv", "pip", "install", version_spec])
            return True
        except subprocess.CalledProcessError:
            return False

    def check_dependencies(self, tool_name: str) -> Dict[str, bool]:
        """Check all dependencies for a tool."""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        status = {}
        for dep in tool.dependencies:
            if dep.type == "pip":
                status[dep.name] = self.check_pip_dependency(dep)
            elif dep.type == "system":
                status[dep.name] = self.check_system_dependency(dep)
        return status

    def ensure_dependencies(
            self, tool_or_name: Union[str, Type, object],
            always_install: bool = False
        ) -> bool:
        """
        Check and optionally install missing dependencies.
        
        Args:
            tool_or_name: Either a tool name, class, or instance
            always_install: Whether to install dependencies without prompting
            
        Returns:
            True if all dependencies are satisfied, False otherwise
        """
        # Find the tool spec
        tool_spec = None
        
        if isinstance(tool_or_name, str):
            # Direct lookup by name
            tool_spec = self.get_tool(tool_or_name)
        elif inspect.isclass(tool_or_name):
            # Lookup by class
            tool_spec = self.get_tool(tool_or_name)
        else:
            # Lookup by instance class
            tool_spec = self.get_tool(tool_or_name.__class__)
            
        if not tool_spec:
            # Skip the dependency check for tools not registered. Up to the user
            # to ensure packages are installed.
            return True

        all_satisfied = True
        for dep in tool_spec.dependencies:
            if dep.type == "pip":
                if not self.is_package_installed(dep.name):
                    if self.auto_install:
                        choice = "y" if always_install else input(f"Install {dep.name}? (y/n)")
                        if choice == "y":
                            success = self.install_pip_dependency(dep)
                            if not success:
                                all_satisfied = False
                        else:
                            all_satisfied = False
                    else:
                        all_satisfied = False
            elif dep.type == "system":
                if not self.check_system_dependency(dep):
                    all_satisfied = False
        return all_satisfied

    def validate_config(self, tool_or_name: Union[str, Type, object], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and process configuration for a tool.
        
        Args:
            tool_or_name: Either a tool name, class, or instance
            config: The configuration to validate
            
        Returns:
            Processed configuration
        """
        tool_spec = self.get_tool(tool_or_name)
        if not tool_spec:
            raise ValueError(f"Tool '{tool_or_name}' not found")

        # Start with provided config
        processed_config = config.copy()

        # Check all requirements
        missing_required = []
        for req in tool_spec.config_requirements:
            if req.key not in config:
                if req.required and req.default is None:
                    missing_required.append(req.key)
                elif req.default is not None:
                    processed_config[req.key] = req.default

        if missing_required:
            raise ValueError(
                f"Tool '{tool_spec.name}' is missing required configuration: {', '.join(missing_required)}"
            )

        return processed_config

    def execute(self, tool_or_name: Union[str, Type, object], config: Dict[str, Any] = None, *args, **kwargs) -> Any:
        """
        Execute a tool, checking dependencies and configuration first.
        
        Args:
            tool_or_name: Either a tool name, class, or instance
            config: Configuration for the tool
            *args, **kwargs: Arguments to pass to the tool
            
        Returns:
            Result of executing the tool
        """
        tool_spec = self.get_tool(tool_or_name)
        if not tool_spec:
            raise ValueError(f"Tool '{tool_or_name}' not found")

        # Check dependencies
        if not self.ensure_dependencies(tool_spec):
            missing = [
                dep.name
                for dep in tool_spec.dependencies
                if (dep.type == "pip" and not self.check_pip_dependency(dep))
                or (dep.type == "system" and not self.check_system_dependency(dep))
            ]
            raise RuntimeError(
                f"Tool '{tool_spec.name}' has missing dependencies: {', '.join(missing)}"
            )

        # Validate and process configuration
        config = config or {}
        processed_config = self.validate_config(tool_spec, config)

    def load_tool(
        self, tool_name: str, requires: List[str] = None, always_install: bool = False
    ) -> Any:
        """
        Load a tool by its fully qualified name.
        
        Args:
            tool_name: Fully qualified name (module.class)
            requires: List of package requirements
            always_install: Whether to install dependencies without prompting
            
        Returns:
            An instance of the tool
        """
        requires = requires or []
        for req in requires:
            dep = Dependency(name=req, type="pip")
            if not self.is_package_installed(dep.name):
                if self.auto_install:
                    if not always_install:
                        choice = input(f"Install {dep.name}? (y/n)")
                        if choice == "y":
                            always_install = True
                    if always_install:
                        success = self.install_pip_dependency(dep)
                        if not success:
                            raise RuntimeError(f"Failed to install {dep.name}")
                            
        module_path, class_name = tool_name.rsplit(".", 1)

        # Import the module
        module = importlib.import_module(module_path)

        # Get the class from the module
        return getattr(module, class_name)()


tool_registry = ToolRegistry(auto_install=True)

# Example usage:
# from agentic.tools.utils.registry import tool_registry
#
# @tool_registry.register(
#     name="weather",
#     description="Get weather information for a location",
#     dependencies=[
#         Dependency("requests", type="pip", version="2.31.0"),
#         Dependency("curl", type="system")
#     ]
# )
# def get_weather(location: str) -> dict:
#     import requests
#     # Example implementation
#     api_key = "your_api_key"
#     url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={location}"
#     response = requests.get(url)
#     return response.json()
