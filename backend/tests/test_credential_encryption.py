from app.core.config import Settings
from app.services.credential_encryption_service import CredentialEncryptionService


def test_encrypts_and_decrypts_refresh_token_without_storing_plaintext() -> None:
    service = CredentialEncryptionService(
        Settings(app_encryption_key="test-encryption-key", app_encryption_key_version="v-test")
    )

    encrypted = service.encrypt("fake-refresh-token")

    assert encrypted != "fake-refresh-token"
    assert "fake-refresh-token" not in encrypted
    assert service.decrypt(encrypted) == "fake-refresh-token"


def test_empty_secret_is_rejected() -> None:
    service = CredentialEncryptionService(Settings(app_encryption_key="test-encryption-key"))

    try:
        service.encrypt("")
    except ValueError as exc:
        assert str(exc) == "Secret value cannot be empty."
    else:
        raise AssertionError("empty secret should be rejected")
