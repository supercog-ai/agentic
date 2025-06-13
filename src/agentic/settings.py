import sqlite3
from pathlib import Path
from typing import Optional, overload, TypeVar

T = TypeVar("T")

class Settings:
    def __init__(self, db_path="agentsdb", cache_dir="~/.agentic", key=None):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(cache_dir).expanduser() / db_path

        connection = self._get_connection()

        # Create tables for both secrets and settings
        connection.cursor().execute(
            "CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value TEXT)"
        )
        connection.commit()
        connection.close()
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def set(self, name, value):
        """Store an unencrypted setting"""
        connection = self._get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO settings (name, value) VALUES (?, ?)",
            (name, str(value)),
        )
        connection.commit()
        connection.close()

    @overload
    def get(self, name) -> Optional[str]:
        return self.get(name, default=None)

    @overload
    def get(self, name: str, default: T) -> T:
        return self.get(name, default=default)

    def get(self, name, default: Optional[T] = None) -> Optional[T]:
        """Retrieve an unencrypted setting"""
        connection = self._get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT value FROM settings WHERE name=?", (name,))
        result = cursor.fetchone()

        connection.close()
        return result[0] if result else default

    def list_settings(self):
        """List all setting names"""
        connection = self._get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT name FROM settings")
        result = [row[0] for row in cursor.fetchall()]

        connection.close()
        return result

    def delete_setting(self, name):
        """Delete a setting"""
        connection = self._get_connection()
        cursor = connection.cursor()

        cursor.execute("DELETE FROM settings WHERE name=?", (name,))
        connection.commit()
        connection.close()

    def __enter__(self):
        return self

# Usage example:
settings = Settings()
