"""
Dashboard management module.

This module provides functions for setting up, running, and managing
the Next.js dashboard.
"""

import subprocess
import sys
import time
import signal
import logging
from typing import Optional

from . import DASHBOARD_ROOT

logger = logging.getLogger(__name__)

# Setup functions
def check_npm_dependencies():
    """
    Check if Node.js and npm are installed.
    
    Returns:
        bool: True if Node.js and npm are installed, False otherwise.
    """
    try:
        node_version = subprocess.run(
            ["node", "--version"], 
            capture_output=True, 
            text=True
        ).stdout.strip()
        npm_version = subprocess.run(
            ["npm", "--version"], 
            capture_output=True, 
            text=True
        ).stdout.strip()
        
        logger.info(f"Found Node.js {node_version} and npm {npm_version}")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error(
            "Node.js or npm not found. The dashboard requires Node.js (v18+) and npm (v8+).\n"
            "Please install them from https://nodejs.org before using the dashboard."
        )
        return False

def install_dependencies():
    """
    Install Node.js dependencies for the dashboard.
    
    Returns:
        bool: True if dependencies were installed successfully, False otherwise.
    """
    if not check_npm_dependencies():
        print("\nThe dashboard requires Node.js and npm to be installed.")
        print("Please install them from https://nodejs.org and try again.")
        return False
    
    logger.info("Installing dashboard dependencies...")
    try:
        subprocess.run(
            ["npm", "install"], 
            cwd=DASHBOARD_ROOT, 
            check=True
        )
        return True
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to install dashboard dependencies: {e}")
        return False

def build_dashboard():
    """
    Build the Next.js dashboard.
    
    Returns:
        bool: True if the dashboard was built successfully, False otherwise.
    """
    if not install_dependencies():
        return False
    
    logger.info("Building dashboard...")
    try:
        subprocess.run(
            ["npm", "run", "build"], 
            cwd=DASHBOARD_ROOT, 
            check=True
        )
        return True
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to build dashboard: {e}")
        return False
    
def run_built_dashboard(port: Optional[int] = None):
    """
    Run the pre-built dashboard without rebuilding it.
    
    Args:
        port (Optional[int]): The port to run the dashboard on.
    
    Returns:
        subprocess.Popen: The process running the dashboard, or None if startup failed.
    """
    print(f"Starting pre-built dashboard on port {port or 3000}...")
    
    if not check_npm_dependencies():
        logger.error("Node.js or npm not found. Required to run the dashboard.")
        return None
    
    command = ["npm", "run", "start"]
    
    if port:
        command.extend(["--", "-p", str(port)])
    
    logger.info(f"Running dashboard with command: {command}")
    
    try:
        process = subprocess.Popen(command, cwd=DASHBOARD_ROOT)
        return process
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to run dashboard: {e}")
        return None

def start_dashboard(port: Optional[int] = None, dev_mode: bool = False):
    """
    Start the Next.js dashboard.
    
    Args:
        port (Optional[int): The port to run the dashboard on.
        dev_mode (bool): Whether to run in development mode.
    
    Returns:
        subprocess.Popen: The process running the dashboard, or None if startup failed.
    """
    command = ["npm", "run"]
    if dev_mode:
        if not install_dependencies():
            return None
        
        command.append("dev")
    else:
        if not build_dashboard():
            return None
        
        command.append("start")

    if port:
        command.extend(["--", "-p", str(port)])

    logger.info(f"Starting dashboard with command: {command}")

    try:
        process = subprocess.Popen(command, cwd=DASHBOARD_ROOT)
        return process
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to start dashboard: {e}")
        return None

# CLI commands
def start_command(port: Optional[int] = None, dev: bool = False):
    """
    Start the dashboard server.
    
    Args:
        port (Optional[int]): The port to run the dashboard on.
        dev (bool): Whether to run in development mode.
    """
    print("\nStarting Agentic Framework Dashboard")
    print("====================================")
    
    if not check_npm_dependencies():
        print(
            "\nError: The dashboard requires Node.js (v18+) and npm (v8+).\n"
            "Please install them from https://nodejs.org and try again."
        )
        sys.exit(1)
    
    dashboard_process = start_dashboard(port=port, dev_mode=dev)
    
    if not dashboard_process:
        sys.exit(1)

    print("\nPress Ctrl+C to stop the dashboard\n")
    
    try:
        # Keep the process running until interrupted
        while dashboard_process.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down dashboard...")
        dashboard_process.send_signal(signal.SIGTERM)
        dashboard_process.wait()
        print("Dashboard stopped")
    
    if dashboard_process.returncode != 0 and dashboard_process.returncode != -signal.SIGTERM.value:
        logger.error(f"Dashboard exited with code {dashboard_process.returncode}")
        sys.exit(dashboard_process.returncode)

def build_command():
    """Build the dashboard for production."""
    print("\nBuilding Agentic Framework Dashboard")
    print("===================================")
    
    if not check_npm_dependencies():
        print(
            "\nError: The dashboard requires Node.js (v18+) and npm (v8+).\n"
            "Please install them from https://nodejs.org and try again."
        )
        sys.exit(1)
    
    if build_dashboard():
        print("\nDashboard built successfully!")
    else:
        print("\nFailed to build dashboard.")
        sys.exit(1)

def run_command(port: Optional[int] = None):
    """
    Run the pre-built dashboard.
    
    Args:
        port (Optional[int]): The port to run the dashboard on.
    """
    print("\nRunning Pre-built Agentic Framework Dashboard")
    print("==========================================")
    
    if not check_npm_dependencies():
        print(
            "\nError: The dashboard requires Node.js (v18+) and npm (v8+).\n"
            "Please install them from https://nodejs.org and try again."
        )
        sys.exit(1)
    
    dashboard_process = run_built_dashboard(port=port)
    
    if not dashboard_process:
        print("\nFailed to run the dashboard.")
        sys.exit(1)
    
    print(f"\nDashboard is running at http://localhost:{port or 3000}")
    print("\nPress Ctrl+C to stop the dashboard\n")
    
    try:
        # Keep the process running until interrupted
        while dashboard_process.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down dashboard...")
        dashboard_process.send_signal(signal.SIGTERM)
        dashboard_process.wait()
        print("Dashboard stopped")
    
    if dashboard_process.returncode != 0 and dashboard_process.returncode != -signal.SIGTERM.value:
        logger.error(f"Dashboard exited with code {dashboard_process.returncode}")
        sys.exit(dashboard_process.returncode)
