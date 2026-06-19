from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import Settings, get_settings


class CredentialEncryptionService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        raw_key = self.settings.app_encryption_key.get_secret_value()
        key_material = hashlib.sha256(raw_key.encode("utf-8")).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(key_material))

    @property
    def key_version(self) -> str:
        return self.settings.app_encryption_key_version

    def encrypt(self, secret_value: str) -> str:
        if not secret_value:
            raise ValueError("Secret value cannot be empty.")

        return self._fernet.encrypt(secret_value.encode("utf-8")).decode("utf-8")

    def decrypt(self, encrypted_value: str) -> str:
        if not encrypted_value:
            raise ValueError("Encrypted value cannot be empty.")

        return self._fernet.decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
