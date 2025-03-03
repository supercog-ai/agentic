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

def start_dashboard(port=3000, dev_mode=False):
    """
    Start the Next.js dashboard.
    
    Args:
        port (int): The port to run the dashboard on.
        dev_mode (bool): Whether to run in development mode.
    
    Returns:
        subprocess.Popen: The process running the dashboard, or None if startup failed.
    """
    if dev_mode:
        if not install_dependencies():
            return None
        
        logger.info(f"Starting dashboard in development mode on port {port}...")
        try:
            process = subprocess.Popen(
                ["npm", "run", "dev", "--", "-p", str(port)],
                cwd=DASHBOARD_ROOT
            )
            return process
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to start dashboard in development mode: {e}")
            return None
    else:
        if not build_dashboard():
            return None
        
        logger.info(f"Starting dashboard on port {port}...")
        try:
            process = subprocess.Popen(
                ["npm", "run", "start", "--", "-p", str(port)],
                cwd=DASHBOARD_ROOT
            )
            return process
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to start dashboard: {e}")
            return None

# CLI commands
def start_command(port=3000, dev=False):
    """
    Start the dashboard server.
    
    Args:
        port (int): The port to run the dashboard on.
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
    
    url = f"http://localhost:{port}"
    print(f"\nDashboard started at {url}")
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

def main():
    """Main CLI entrypoint."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agentic Framework Dashboard")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the dashboard")
    start_parser.add_argument(
        "--port", "-p", type=int, default=3000, help="Port to run the dashboard on"
    )
    start_parser.add_argument(
        "--dev", action="store_true", help="Run in development mode"
    )
    
    # Build command
    build_parser = subparsers.add_parser("build", help="Build the dashboard")
    
    args = parser.parse_args()
    
    if args.command == "start":
        start_command(port=args.port, dev=args.dev)
    elif args.command == "build":
        build_command()
    else:
        parser.print_help()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
