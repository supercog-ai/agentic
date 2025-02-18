import os
import subprocess
import sqlite3
from pathlib import Path
import base64
import hashlib
from typing import Optional

# from cryptography.fernet import Fernet

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from os import urandom


class FastEncryptor:
    def __init__(self, key):
        self.cipher = ChaCha20Poly1305(key)

    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode()
        nonce = urandom(12)
        return nonce + self.cipher.encrypt(nonce, data, None)

    def decrypt(self, data):
        try:
            nonce = data[:12]
            ciphertext = data[12:]
            return self.cipher.decrypt(nonce, ciphertext, None).decode()
        except Exception as e:
            # print(f"Error decrypting data: {e}")
            return None


def get_machine_id():
    if os.name == "nt":  # Windows
        output = subprocess.check_output("wmic csproduct get UUID", shell=True)
        return output.decode().split("\n")[1].strip()
    elif os.path.exists("/etc/machine-id"):  # Linux/macOS
        return open("/etc/machine-id").read().strip()
    else:  # macOS alternative
        output = subprocess.check_output(
            ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]
        )
        for line in output.decode().split("\n"):
            if "IOPlatformUUID" in line:
                return line.split('"')[-2]
    return None


def generate_fernet_key():
    """Generate a valid Fernet key from machine-specific data."""
    machine_id = get_machine_id()
    if not machine_id:
        raise ValueError("Could not determine machine ID")

    # Hash the machine ID to create a deterministic 32-byte key
    hashed_id = hashlib.sha256(machine_id.encode()).digest()[:32]  # Take first 32 bytes

    # Base64 encode to make it a valid Fernet key
    fernet_key = base64.urlsafe_b64encode(hashed_id)

    return hashed_id


class SecretManager:
    def __init__(self, db_path="agentsdb", cache_dir="~/.agentic", key=None):
        self.db_path = Path(cache_dir).expanduser() / db_path
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.key = key
        self.encrypter = FastEncryptor(key)

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS secrets (name TEXT PRIMARY KEY, value TEXT)"
        )
        conn.commit()
        return conn, cursor

    def set_secret(self, name, value):
        conn, cursor = self._get_connection()
        try:
            encrypted_value = self.encrypter.encrypt(value.encode())
            cursor.execute(
                "INSERT OR REPLACE INTO secrets (name, value) VALUES (?, ?)",
                (name, encrypted_value),
            )
            conn.commit()
        finally:
            conn.close()

    def get_secret(self, name, default_value: Optional[str] = None):
        conn, cursor = self._get_connection()
        try:
            cursor.execute("SELECT value FROM secrets WHERE name=?", (name,))
            result = cursor.fetchone()
            if result:
                return self.encrypter.decrypt(result[0])
            elif os.environ.get(name):
                return os.environ.get(name)
            elif default_value is not None:
                return default_value
        finally:
            conn.close()

    def get_all_secrets(self) -> list[tuple[str, str]]:
        res = []
        for secret in self.list_secrets():
            res.append((secret, self.get_secret(secret)))
        return res

    def list_secrets(self):
        conn, cursor = self._get_connection()
        try:
            cursor.execute("SELECT name FROM secrets")
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_required_secret(self, name) -> str:
        val = self.get_secret(name)
        if val is None:
            raise ValueError(f"Secret '{name}' is not set")
        return val

    def delete_secret(self, name):
        conn, cursor = self._get_connection()
        try:
            cursor.execute("DELETE FROM secrets WHERE name=?", (name,))
            conn.commit()
        finally:
            conn.close()

    def copy_secrets_to_env(self):
        for secret in self.list_secrets():
            value = self.get_secret(secret)
            if value:
                os.environ[secret] = value


agentic_secrets = SecretManager(key=generate_fernet_key())
