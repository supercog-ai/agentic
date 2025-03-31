from dataclasses import dataclass
from typing import List, Callable, Optional, Dict, Any, Type
import importlib
import importlib.util

import shutil
import subprocess
from contextlib import contextmanager

from agentic.tools.base import BaseAgenticTool


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
        self.tools: Dict[Type, Tool] = {}
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
            if isinstance(target, type):
                self.tools[target] = Tool(
                    name=name,
                    description=description,
                    function=target,
                    dependencies=dependencies or [],
                    config_requirements=config_requirements or [],
                )
                return target
            else:
                self.tools[target] = Tool(
                    name=name,
                    description=description,
                    function=target,
                    dependencies=dependencies or [],
                    config_requirements=config_requirements or [],
                )
                return target

        return decorator

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
        tool = self.tools.get(tool_name)
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
            self, tool,
            always_install: bool = False
        ) -> bool:
        """Check and optionally install missing dependencies."""
        if hasattr(tool, "__class__"):
            toolcls = tool.__class__
            while True:
                tool_spec = self.tools.get(toolcls)
                if tool_spec:
                    break
                toolcls = toolcls.__bases__[0]
                if toolcls in [BaseAgenticTool, object]:
                    break
        else:
            tool_spec = self.tools.get(tool)
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

    def validate_config(self, tool, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and process configuration for a tool."""
        tool = self.tools.get(tool)
        if not tool:
            raise ValueError(f"Tool '{tool}' not found")

        # Start with provided config
        processed_config = config.copy()

        # Check all requirements
        missing_required = []
        for req in tool.config_requirements:
            if req.key not in config:
                if req.required and req.default is None:
                    missing_required.append(req.key)
                elif req.default is not None:
                    processed_config[req.key] = req.default

        if missing_required:
            raise ValueError(
                f"Tool '{tool}' is missing required configuration: {', '.join(missing_required)}"
            )

        return processed_config

    def execute(self, tool: Any, config: Dict[str, Any] = None, *args, **kwargs) -> Any:
        """Execute a tool, checking dependencies and configuration first."""
        if hasattr(tool, "__class__"):
            tool_spec = self.tools.get(tool.__class__)
        else:
            tool_spec = self.tools.get(tool)
        if not tool_spec:
            raise ValueError(f"Tool '{tool}' not found")

        # Check dependencies
        if not self.ensure_dependencies(tool_spec):
            missing = [
                dep.name
                for dep in tool_spec.dependencies
                if (dep.type == "pip" and not self.check_pip_dependency(dep))
                or (dep.type == "system" and not self.check_system_dependency(dep))
            ]
            raise RuntimeError(
                f"Tool '{tool}' has missing dependencies: {', '.join(missing)}"
            )

        # Validate and process configuration
        config = config or {}
        processed_config = self.validate_config(tool_spec, config)

    def load_tool(
        self, tool_name: str, requires: List[str] = None, always_install: bool = False
    ) -> Tool:
        for req in requires:
            dep = Dependency(name=req, type="pip")
            if not self.is_package_installed(dep.name):
                if self.auto_install:
                    if not always_install:
                        choice = input(f"Install {dep}? (y/n)")
                        if choice == "y":
                            always_install = True
                    if always_install:
                        success = self.install_pip_dependency(dep)
                        if not success:
                            raise RuntimeError(f"Failed to install {dep}")
        module_path, class_name = tool_name.rsplit(".", 1)

        # Import the module
        module = importlib.import_module(module_path)

        # Get the class from the module
        return getattr(module, class_name)()


# Example usage:
tool_registry = ToolRegistry(auto_install=True)

# @registry.register(
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
