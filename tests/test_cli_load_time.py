import time
import pytest
from typer.testing import CliRunner
import importlib
import sys

def test_module_import_time():
    """Test that the CLI module imports quickly"""
    # Remove the module if it's already imported
    if 'your_cli_module' in sys.modules:
        del sys.modules['your_cli_module']
    
    # Measure import time
    start_time = time.perf_counter()
    import agentic.cli  # Replace with actual module name
    end_time = time.perf_counter()
    
    import_time = end_time - start_time
    print(f"\nModule import time: {import_time:.3f} seconds")
    
    # Assert import time is under threshold (adjust as needed)
    assert import_time < 1.0, f"Module import took too long: {import_time:.3f} seconds"
