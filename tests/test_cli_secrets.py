import pytest
import os
from pathlib import Path
from unittest.mock import patch
import tempfile

from agentic.cli import secrets_set, secrets_list, secrets_get, secrets_delete
from agentic.agentic_secrets import agentic_secrets

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture
def mock_typer():
    """Mock typer"""
    with patch('typer.echo') as mock:
        yield mock

@pytest.fixture(autouse=True)
def setup_test_db(temp_dir):
    """Setup a test database for secrets"""
    # Override the database path for testing
    agentic_secrets.db_path = temp_dir / "test_secrets.db"
    agentic_secrets.cache_dir = temp_dir
    agentic_secrets.cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a new database connection
    agentic_secrets._get_connection()
    
    yield
    
    # Cleanup
    if agentic_secrets.db_path.exists():
        agentic_secrets.db_path.unlink()

def test_secrets_set(mock_typer):
    """Test setting a secret"""
    # Test with explicit value
    secrets_set("TEST_SECRET", "test_value")
    assert agentic_secrets.get_secret("TEST_SECRET") == "test_value"
    mock_typer.assert_called_with(None)  # set_secret returns None
    
    # Test with value in name=value format
    secrets_set("TEST_SECRET2=test_value2")
    assert agentic_secrets.get_secret("TEST_SECRET2") == "test_value2"
    mock_typer.assert_called_with(None)  # set_secret returns None

def test_secrets_list(mock_typer):
    """Test listing secrets"""
    # Set up some test secrets
    agentic_secrets.set_secret("SECRET1", "value1")
    agentic_secrets.set_secret("SECRET2", "value2")
    
    # Test listing without values
    secrets_list(values=False)
    mock_typer.assert_called_with("SECRET1\nSECRET2")
    
    # Test listing with values
    secrets_list(values=True)
    mock_typer.assert_called_with(agentic_secrets.get_all_secrets())  # List of tuples

def test_secrets_get(mock_typer):
    """Test getting a secret"""
    # Set up a test secret
    agentic_secrets.set_secret("TEST_SECRET", "test_value")
    
    # Test getting existing secret
    secrets_get("TEST_SECRET")
    mock_typer.assert_called_with("test_value")
    
    # Test getting non-existent secret
    secrets_get("NONEXISTENT")
    mock_typer.assert_called_with(None)

def test_secrets_delete(mock_typer):
    """Test deleting a secret"""
    # Set up a test secret
    agentic_secrets.set_secret("TEST_SECRET", "test_value")
    
    # Test deleting existing secret
    secrets_delete("TEST_SECRET")
    assert agentic_secrets.get_secret("TEST_SECRET") is None
    mock_typer.assert_called_with(None)  # delete_secret returns None
    
    # Test deleting non-existent secret
    secrets_delete("NONEXISTENT")
    mock_typer.assert_called_with(None)  # delete_secret returns None

def test_secrets_environment_variables():
    """Test that secrets are properly handled from environment variables"""
    # Set up environment variable
    os.environ["ENV_SECRET"] = "env_value"
    
    # Test getting environment variable
    assert agentic_secrets.get_secret("ENV_SECRET") == "env_value"
    
    # Clean up
    del os.environ["ENV_SECRET"]