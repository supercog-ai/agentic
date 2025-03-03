"""
Agentic Framework Dashboard

This package provides a Next.js-based dashboard for monitoring and interacting with
agentic-framework agents.
"""

import importlib.metadata
from pathlib import Path

# Define the version
__version__ = "0.1.0"

# Package root directory
DASHBOARD_ROOT = Path(__file__).parent.absolute()

def is_installed():
    """Check if the dashboard package is installed."""
    try:
        importlib.metadata.distribution("agentic-framework")
        return True
    except importlib.metadata.PackageNotFoundError:
        return False