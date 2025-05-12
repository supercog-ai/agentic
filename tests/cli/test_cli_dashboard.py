import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from agentic.cli import app

runner = CliRunner()

@pytest.fixture
def mock_dashboard_imports():
    """Mock dashboard-related imports and checks"""
    with patch('agentic.cli.import_module') as mock_import:
        yield mock_import

@pytest.fixture
def mock_dashboard_setup():
    """Mock dashboard setup functions"""
    with patch('agentic.dashboard.setup.check_npm_dependencies') as mock_check_deps, \
         patch('agentic.dashboard.setup.start_dashboard') as mock_start, \
         patch('agentic.dashboard.setup.build_dashboard') as mock_build:
        
        # Configure default return values
        mock_check_deps.return_value = True
        mock_start.return_value = MagicMock()
        mock_build.return_value = True
        
        yield {
            'check_deps': mock_check_deps,
            'start': mock_start,
            'build': mock_build
        }

def test_dashboard_start_success(mock_dashboard_imports, mock_dashboard_setup):
    """Test successful dashboard start command"""
    # Mock process that exits after first sleep
    mock_process = MagicMock()
    mock_process.poll.side_effect = [None, 0]
    mock_process.returncode = 0
    mock_dashboard_setup['start'].return_value = mock_process
    
    with patch('time.sleep') as mock_sleep, \
         patch('signal.SIGTERM') as mock_sigterm:
        # Mock SIGTERM signal value
        mock_sigterm.value = 15
        result = runner.invoke(app, ['dashboard', 'start'])
    
    assert result.exit_code == 0
    mock_dashboard_setup['check_deps'].assert_called_once()
    mock_dashboard_setup['start'].assert_called_once_with(port=None, dev_mode=False)

def test_dashboard_start_with_options(mock_dashboard_imports, mock_dashboard_setup):
    """Test dashboard start with custom port and dev mode"""
    mock_process = MagicMock()
    mock_process.poll.side_effect = [None, 0]
    mock_process.returncode = 0
    mock_dashboard_setup['start'].return_value = mock_process
    
    with patch('time.sleep') as mock_sleep, \
         patch('signal.SIGTERM') as mock_sigterm:
        # Mock SIGTERM signal value
        mock_sigterm.value = 15
        result = runner.invoke(app, ['dashboard', 'start', '--port', '3001', '--dev'])
    
    assert result.exit_code == 0
    mock_dashboard_setup['start'].assert_called_once_with(port=3001, dev_mode=True)

def test_dashboard_start_missing_dependencies(mock_dashboard_imports, mock_dashboard_setup):
    """Test dashboard start when dependencies are missing"""
    mock_dashboard_setup['check_deps'].return_value = False
    
    result = runner.invoke(app, ['dashboard', 'start'])
    
    assert result.exit_code == 1
    assert "Node.js" in result.stdout
    mock_dashboard_setup['start'].assert_not_called()

def test_dashboard_start_process_failure(mock_dashboard_imports, mock_dashboard_setup):
    """Test dashboard start when process fails to start"""
    mock_dashboard_setup['start'].return_value = None
    
    result = runner.invoke(app, ['dashboard', 'start'])
    
    assert result.exit_code == 1

def test_dashboard_build_success(mock_dashboard_imports, mock_dashboard_setup):
    """Test successful dashboard build command"""
    result = runner.invoke(app, ['dashboard', 'build'])
    
    assert result.exit_code == 0
    mock_dashboard_setup['check_deps'].assert_called_once()
    mock_dashboard_setup['build'].assert_called_once()

def test_dashboard_build_missing_dependencies(mock_dashboard_imports, mock_dashboard_setup):
    """Test dashboard build when dependencies are missing"""
    mock_dashboard_setup['check_deps'].return_value = False
    
    result = runner.invoke(app, ['dashboard', 'build'])
    
    assert result.exit_code == 1
    assert "Node.js" in result.stdout
    mock_dashboard_setup['build'].assert_not_called()

def test_dashboard_build_failure(mock_dashboard_imports, mock_dashboard_setup):
    """Test dashboard build when build process fails"""
    mock_dashboard_setup['build'].return_value = False
    
    result = runner.invoke(app, ['dashboard', 'build'])
    
    assert result.exit_code == 1
    assert "Failed" in result.stdout

def test_dashboard_command_without_package(mock_dashboard_imports):
    """Test dashboard command when dashboard package is not installed"""
    mock_dashboard_imports.side_effect = ImportError()
    
    result = runner.invoke(app, ['dashboard', 'start'])
    
    assert result.exit_code == 1
    assert "not installed" in result.stdout

def test_dashboard_run_success(mock_dashboard_imports, mock_dashboard_setup):
    """Test successful dashboard run command without rebuilding"""
    # Create a mock for the run_built_dashboard function
    with patch('agentic.dashboard.setup.run_built_dashboard') as mock_run, \
         patch('time.sleep') as mock_sleep, \
         patch('signal.SIGTERM') as mock_sigterm, \
         patch('threading.Thread') as mock_thread:
        
        # Mock process that exits after first sleep
        mock_process = MagicMock()
        mock_process.poll.side_effect = [None, 0]
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Mock SIGTERM signal value
        mock_sigterm.value = 15
        
        # Test the basic run command
        result = runner.invoke(app, ['dashboard', 'run'])
    
    assert result.exit_code == 0
    mock_dashboard_setup['check_deps'].assert_called_once()
    mock_run.assert_called_once_with(port=3000)
    # Thread shouldn't be created without agent_path
    mock_thread.assert_not_called()

def test_dashboard_run_with_custom_port(mock_dashboard_imports, mock_dashboard_setup):
    """Test dashboard run with custom port"""
    with patch('agentic.dashboard.setup.run_built_dashboard') as mock_run, \
         patch('time.sleep') as mock_sleep, \
         patch('signal.SIGTERM') as mock_sigterm:
        
        # Mock process that exits after first sleep
        mock_process = MagicMock()
        mock_process.poll.side_effect = [None, 0]
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Mock SIGTERM signal value
        mock_sigterm.value = 15
        
        # Test with custom port
        result = runner.invoke(app, ['dashboard', 'run', '--port', '4000'])
    
    assert result.exit_code == 0
    mock_run.assert_called_once_with(port=4000)

def test_dashboard_run_with_agent(mock_dashboard_imports, mock_dashboard_setup):
    """Test dashboard run with agent in background thread"""
    with patch('agentic.dashboard.setup.run_built_dashboard') as mock_run, \
         patch('time.sleep') as mock_sleep, \
         patch('signal.SIGTERM') as mock_sigterm, \
         patch('threading.Thread') as mock_thread, \
         patch('agentic.cli.serve') as mock_serve:
        
        # Mock process that exits after first sleep
        mock_process = MagicMock()
        mock_process.poll.side_effect = [None, 0]
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Mock thread instance
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Mock SIGTERM signal value
        mock_sigterm.value = 15
        
        # Test with agent path
        result = runner.invoke(app, ['dashboard', 'run', '--agent-path', 'agent.py'])
    
    assert result.exit_code == 0
    mock_run.assert_called_once_with(port=3000)
    
    # Thread should be created with agent_path
    mock_thread.assert_called_once()
    # Verify thread arguments
    args, kwargs = mock_thread.call_args
    assert kwargs['target'] == mock_serve
    assert kwargs['args'] == ['agent.py', False, 8086, False]
    assert kwargs['daemon'] is True
    
    # Verify thread was started
    mock_thread_instance.start.assert_called_once()

def test_dashboard_run_with_all_options(mock_dashboard_imports, mock_dashboard_setup):
    """Test dashboard run with all available options"""
    with patch('agentic.dashboard.setup.run_built_dashboard') as mock_run, \
         patch('time.sleep') as mock_sleep, \
         patch('signal.SIGTERM') as mock_sigterm, \
         patch('threading.Thread') as mock_thread, \
         patch('agentic.cli.serve') as mock_serve:
        
        # Mock process that exits after first sleep
        mock_process = MagicMock()
        mock_process.poll.side_effect = [None, 0]
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Mock thread instance
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Mock SIGTERM signal value
        mock_sigterm.value = 15
        
        # Test with all options
        result = runner.invoke(app, [
            'dashboard', 'run', 
            '--port', '5000', 
            '--agent-path', 'myagent.py',
            '--agent-port', '9000',
            '--use-ray', 
            '--user-agents'
        ])
    
    assert result.exit_code == 0
    mock_run.assert_called_once_with(port=5000)
    
    # Thread should be created with all options
    mock_thread.assert_called_once()
    # Verify thread arguments
    args, kwargs = mock_thread.call_args
    assert kwargs['target'] == mock_serve
    assert kwargs['args'] == ['myagent.py', True, 9000, True]
    assert kwargs['daemon'] is True
    
    # Verify thread was started
    mock_thread_instance.start.assert_called_once()

def test_dashboard_run_missing_dependencies(mock_dashboard_imports, mock_dashboard_setup):
    """Test dashboard run when dependencies are missing"""
    mock_dashboard_setup['check_deps'].return_value = False
    
    result = runner.invoke(app, ['dashboard', 'run'])
    
    assert result.exit_code == 1
    assert "Node.js" in result.stdout

def test_dashboard_run_process_failure(mock_dashboard_imports, mock_dashboard_setup):
    """Test dashboard run when process fails to start"""
    with patch('agentic.dashboard.setup.run_built_dashboard') as mock_run:
        mock_run.return_value = None
        
        result = runner.invoke(app, ['dashboard', 'run'])
    
    assert result.exit_code == 1
    assert "Failed" in result.stdout
