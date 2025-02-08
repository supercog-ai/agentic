import pytest
import os
import subprocess
import sqlite3
from pathlib import Path
import base64
import hashlib
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet
from agentic.agentic_secrets import SecretManager, get_machine_id, generate_fernet_key


# Test fixtures
@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path for testing."""
    return str(tmp_path / "test.db")


@pytest.fixture
def mock_machine_id():
    """Mock machine ID for consistent testing."""
    return "test-machine-id-12345"


@pytest.fixture
def test_fernet_key():
    """Create a consistent Fernet key for testing."""
    return Fernet.generate_key()


@pytest.fixture
def secret_manager(temp_db_path, test_fernet_key):
    """Create a SecretManager instance with test configuration."""
    return SecretManager(db_path=temp_db_path, key=test_fernet_key)


# Tests for get_machine_id
@pytest.mark.parametrize(
    "os_name,machine_id",
    [
        ("nt", "windows-uuid"),
        ("posix", "linux-machine-id"),
    ],
)
def test_get_machine_id(os_name, machine_id):
    with patch("os.name", os_name):
        if os_name == "nt":
            mock_output = MagicMock()
            mock_output.decode.return_value = f"UUID\n{machine_id}\n"
            with patch("subprocess.check_output", return_value=mock_output):
                assert get_machine_id() == machine_id
        else:
            with (
                patch("os.path.exists", return_value=True),
                patch(
                    "builtins.open",
                    MagicMock(return_value=MagicMock(read=lambda: machine_id)),
                ),
            ):
                assert get_machine_id() == machine_id


def test_get_machine_id_macos():
    with (
        patch("os.name", "posix"),
        patch("os.path.exists", return_value=False),
        patch("subprocess.check_output") as mock_subprocess,
    ):
        mock_subprocess.return_value = b'IOPlatformUUID = "macos-uuid-12345"'
        assert get_machine_id() == "macos-uuid-12345"


# Tests for generate_fernet_key
def test_generate_fernet_key(mock_machine_id):
    with patch("agentic.agentic_secrets.get_machine_id", return_value=mock_machine_id):
        key = generate_fernet_key()
        assert len(key) == 44  # Standard Fernet key length
        assert isinstance(key, bytes)
        # Test key is valid for Fernet
        Fernet(key)  # Should not raise an error


def test_generate_fernet_key_no_machine_id():
    with patch("agentic.agentic_secrets.get_machine_id", return_value=None):
        with pytest.raises(ValueError, match="Could not determine machine ID"):
            generate_fernet_key()


# Tests for SecretManager
def test_secret_manager_init(secret_manager, temp_db_path):
    """Test SecretManager initialization creates database and table."""
    assert os.path.exists(temp_db_path)
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='secrets'"
    )
    assert cursor.fetchone() is not None
    conn.close()


def test_set_and_get_secret(secret_manager):
    """Test setting and retrieving a secret."""
    secret_name = "test_secret"
    secret_value = "test_value"

    secret_manager.set_secret(secret_name, secret_value)
    retrieved_value = secret_manager.get_secret(secret_name)

    assert retrieved_value == secret_value


def test_get_nonexistent_secret(secret_manager):
    """Test retrieving a non-existent secret returns None."""
    assert secret_manager.get_secret("nonexistent") is None


def test_list_secrets(secret_manager):
    """Test listing all secrets."""
    secrets = {"secret1": "value1", "secret2": "value2", "secret3": "value3"}

    for name, value in secrets.items():
        secret_manager.set_secret(name, value)

    secret_list = secret_manager.list_secrets()
    assert len(secret_list) == len(secrets)
    assert all(name in secret_list for name in secrets.keys())


def test_delete_secret(secret_manager):
    """Test deleting a secret."""
    secret_name = "test_secret"
    secret_value = "test_value"

    secret_manager.set_secret(secret_name, secret_value)
    assert secret_manager.get_secret(secret_name) == secret_value

    secret_manager.delete_secret(secret_name)
    assert secret_manager.get_secret(secret_name) is None


def test_encryption_different_instances(temp_db_path, test_fernet_key):
    """Test that two instances with the same key can encrypt/decrypt each other's secrets."""
    manager1 = SecretManager(db_path=temp_db_path, key=test_fernet_key)
    manager2 = SecretManager(db_path=temp_db_path, key=test_fernet_key)

    secret_name = "test_secret"
    secret_value = "test_value"

    manager1.set_secret(secret_name, secret_value)
    assert manager2.get_secret(secret_name) == secret_value


@pytest.mark.parametrize(
    "secret_value",
    [
        "simple string",
        "Special chars: !@#$%^&*()",
        "Unicode: 你好世界",
        "Very long string" * 1000,
    ],
)
def test_secret_values(secret_manager, secret_value):
    """Test storing and retrieving various types of secret values."""
    secret_name = "test_secret"
    secret_manager.set_secret(secret_name, secret_value)
    assert secret_manager.get_secret(secret_name) == secret_value


def test_concurrent_access(temp_db_path, test_fernet_key):
    """Test that multiple SecretManager instances can access the same database."""
    managers = [
        SecretManager(db_path=temp_db_path, key=test_fernet_key) for _ in range(3)
    ]

    # Each manager sets a secret
    for i, manager in enumerate(managers):
        manager.set_secret(f"secret{i}", f"value{i}")

    # Each manager should be able to read all secrets
    for manager in managers:
        for i in range(len(managers)):
            assert manager.get_secret(f"secret{i}") == f"value{i}"
