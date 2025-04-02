import pytest
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import importlib.util
import sys

from agentic.cli import find_agent_instances, copy_examples
from agentic.common import Agent
from agentic.settings import settings
from agentic.agentic_secrets import agentic_secrets

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def mock_console():
    """Mock the rich console"""
    with patch('rich.console.Console') as mock:
        console = MagicMock()
        mock.return_value = console
        yield console

@pytest.fixture
def mock_status():
    """Mock the rich status context manager"""
    with patch('rich.status.Status') as mock:
        status = MagicMock()
        status.__enter__.return_value = status
        status.__exit__.return_value = None
        mock.return_value = status
        yield status

@pytest.fixture
def mock_resources():
    """Mock importlib.resources"""
    with patch('importlib.resources.path') as mock:
        mock.return_value.__enter__.return_value = Path("mock_examples")
        yield mock

@pytest.fixture
def mock_agent():
    """Create a mock agent for testing"""
    return Agent(
        name="Test Agent",
        instructions="Test instructions",
        tools=[],
        model="test-model"
    )

def test_init_command(temp_dir, mock_console, mock_status, mock_resources):
    """Test the init command"""
    from agentic.cli import init
    
    # Create mock examples directory
    mock_examples_dir = temp_dir / "mock_examples"
    mock_examples_dir.mkdir()
    (mock_examples_dir / "example1.py").write_text("print('example1')")
    (mock_examples_dir / "example2.py").write_text("print('example2')")
    
    # Update the mock to return our temp examples directory
    mock_resources.return_value.__enter__.return_value = mock_examples_dir
    
    # Create test destination
    test_dest = temp_dir / "test_project"
    test_dest.mkdir()
    
    # Run init command
    init(str(test_dest))
    
    # Verify directory structure was created
    assert (test_dest / "agents").exists()
    assert (test_dest / "tools").exists()
    assert (test_dest / "tests").exists()
    assert (test_dest / "runtime").exists()
    
    # Verify examples were copied
    assert (test_dest / "examples" / "example1.py").exists()
    assert (test_dest / "examples" / "example2.py").exists()

def test_init_runtime_directory(temp_dir):
    """Test the init_runtime_directory command"""
    from agentic.cli import init_runtime_directory
    
    test_runtime = temp_dir / "test_runtime"
    
    # Run init_runtime_directory command
    init_runtime_directory(str(test_runtime))
    
    # Verify runtime directory was created
    assert test_runtime.exists()
    
    # Verify setting was added
    assert settings.get("AGENTIC_RUNTIME_DIR") == str(test_runtime.resolve())

def test_find_agent_instances(temp_dir, mock_agent):
    """Test finding agent instances in a module"""
    # Create a test module with an agent instance
    test_module = temp_dir / "test_agent.py"
    test_module.write_text("""
from agentic.common import Agent

agent = Agent(
    name="Test Agent",
    instructions="Test instructions",
    tools=[],
    model="test-model"
)
""")
    
    # Test finding agent instances
    agents = find_agent_instances(str(test_module))
    assert len(agents) == 1
    assert isinstance(agents[0], Agent)
    assert agents[0].name == "Test Agent"

def test_copy_examples(temp_dir, mock_console):
    """Test copying example files"""
    # Create source directory with test files
    src_path = temp_dir / "src"
    src_path.mkdir()
    (src_path / "file1.txt").write_text("test1")
    (src_path / "file2.txt").write_text("test2")
    
    # Create destination directory
    dest_path = temp_dir / "dest"
    dest_path.mkdir()
    
    # Test copying examples
    copy_examples(src_path, dest_path, mock_console)
    
    # Verify files were copied
    assert (dest_path / "file1.txt").exists()
    assert (dest_path / "file2.txt").exists()
    
    # Verify console was called
    mock_console.print.assert_called()

def test_shell_command():
    """Test the shell command"""
    from agentic.cli import shell
    
    # Mock os.execvp
    with patch('os.execvp') as mock_execvp:
        shell(["echo", "test"])
        mock_execvp.assert_called_once_with("sh", ["sh", "-c", "echo test"])

def test_thread_command(temp_dir, mock_agent):
    """Test the thread command"""
    from agentic.cli import thread
    
    # Create a test agent file
    test_agent_file = temp_dir / "test_agent.py"
    test_agent_file.write_text("""
from agentic.common import Agent

agent = Agent(
    name="Test Agent",
    instructions="Test instructions",
    tools=[],
    model="test-model"
)
""")
    
    # Mock AgentRunner
    with patch('agentic.common.AgentRunner') as mock_runner:
        mock_runner_instance = MagicMock()
        mock_runner.return_value = mock_runner_instance
        
        # Test thread command
        thread(str(test_agent_file))
        
        # Verify AgentRunner was created and repl_loop was called
        mock_runner.assert_called_once()
        mock_runner_instance.repl_loop.assert_called_once()

def test_serve_command(temp_dir, mock_agent):
    """Test the serve command"""
    from agentic.cli import serve
    
    # Create a test agent file
    test_agent_file = temp_dir / "test_agent.py"
    test_agent_file.write_text("""
from agentic.common import Agent

agent = Agent(
    name="Test Agent",
    instructions="Test instructions",
    tools=[],
    model="test-model"
)
""")
    
    # Mock AgentAPIServer
    with patch('agentic.api.AgentAPIServer') as mock_server:
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance
        
        # Test serve command
        serve(str(test_agent_file), port=8086)
        
        # Verify AgentAPIServer was created and run was called
        mock_server.assert_called_once()
        mock_server_instance.run.assert_called_once()

def test_streamlit_command():
    """Test the streamlit command"""
    from agentic.cli import app
    from typer.testing import CliRunner
    
    runner = CliRunner()
    
    # Mock os.execvp
    with patch('os.execvp') as mock_execvp:
        # Call streamlit command through the CLI runner
        result = runner.invoke(app, ["streamlit"])
            
        # Verify execvp was called with correct arguments
        mock_execvp.assert_called_once_with(
            "streamlit", 
            ["streamlit", "run", "src/agentic/streamlit/app.py"]
        )