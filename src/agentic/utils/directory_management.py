import os
from pathlib import Path
from agentic.settings import settings

def get_runtime_directory():
    """
    Gets or creates a consistent runtime directory for agentic.
    Returns the path to the runtime directory.
    """    
    # If environment variable already exists, use it
    if 'AGENTIC_RUNTIME_DIR' in os.environ:
        runtime_dir = os.environ['AGENTIC_RUNTIME_DIR']
    elif 'AGENTIC_RUNTIME_DIR' in settings.list_settings():
        runtime_dir = settings.get('AGENTIC_RUNTIME_DIR')
    else:
        # Look for a runtime directory in the current directory, otherwise use the agentic package directory
        current_dir = Path.cwd()
        runtime_dir = current_dir / "runtime"
        if not runtime_dir.exists():
            # Get the agentic package directory path
            import agentic
            agentic_dir = os.path.dirname(os.path.dirname(os.path.abspath(agentic.__file__)))
            
            # Create runtime directory path
            runtime_dir = os.path.join(agentic_dir, "runtime")
    
    # Create the directory if it doesn't exist
    os.makedirs(runtime_dir, exist_ok=True)
    
    return runtime_dir

def get_runtime_filepath(filename):
    """
    Returns the path to the runtime file.
    """
    runtime_dir = get_runtime_directory()
    return os.path.join(runtime_dir, filename)