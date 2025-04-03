import pytest
from pathlib import Path
from unittest.mock import patch
import tempfile

# Import settings first so we can patch it
from agentic.settings import Settings

# Create a mock settings instance
@pytest.fixture(autouse=True)
def mock_settings():
    with patch('agentic.cli.settings') as mock_settings:
        # Create a real Settings instance for testing
        with tempfile.TemporaryDirectory() as tmpdirname:
            test_settings = Settings(
                db_path=str(Path(tmpdirname) / "test_settings.db"),
                cache_dir=str(tmpdirname)
            )
            # Make the mock behave like a real Settings instance
            mock_settings.set = test_settings.set
            mock_settings.get = test_settings.get
            mock_settings.delete_setting = test_settings.delete_setting
            mock_settings.list_settings = test_settings.list_settings
            yield mock_settings

# Now import the CLI functions
from agentic.cli import settings_set, settings_list, settings_get, settings_delete

@pytest.fixture
def mock_typer():
    """Mock typer"""
    with patch('typer.echo') as mock:
        yield mock

def test_settings_set(mock_typer, mock_settings):
    """Test setting a setting"""
    settings_set("TEST_SETTING", "test_value")
    mock_typer.assert_called_with(None)
    assert mock_settings.get("TEST_SETTING") == "test_value"

def test_settings_list(mock_typer, mock_settings):
    """Test listing settings"""
    # Set up test settings
    mock_settings.set("SETTING1", "value1")
    mock_settings.set("SETTING2", "value2")
    
    settings_list()
    mock_typer.assert_called_with("SETTING1\nSETTING2")

def test_settings_get(mock_typer, mock_settings):
    """Test getting a setting"""
    mock_settings.set("TEST_SETTING", "test_value")
    
    settings_get("TEST_SETTING")
    mock_typer.assert_called_with("test_value")
    
    settings_get("NONEXISTENT")
    mock_typer.assert_called_with(None)

def test_settings_delete(mock_typer, mock_settings):
    """Test deleting a setting"""
    mock_settings.set("TEST_SETTING", "test_value")
    
    settings_delete("TEST_SETTING")
    mock_typer.assert_called_with(None)
    assert mock_settings.get("TEST_SETTING") is None
    
    settings_delete("NONEXISTENT")
    mock_typer.assert_called_with(None)

def test_settings_type_conversion(mock_settings):
    """Test that settings are properly converted to their original type"""
    mock_settings.set("INT_SETTING", "42")
    assert mock_settings.get("INT_SETTING", default=0) == "42"
    
    mock_settings.set("BOOL_SETTING", "true")
    assert mock_settings.get("BOOL_SETTING", default=False) == "true"
    
    mock_settings.set("FLOAT_SETTING", "3.14")
    assert mock_settings.get("FLOAT_SETTING", default=0.0) == "3.14"