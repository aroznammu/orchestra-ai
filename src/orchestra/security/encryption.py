"""Token encryption using Fernet symmetric encryption."""

from cryptography.fernet import Fernet, InvalidToken

from orchestra.config import get_settings


def _get_fernet() -> Fernet:
    settings = get_settings()
    key = settings.fernet_key.get_secret_value()
    if key.startswith("CHANGE-ME"):
        key = Fernet.generate_key().decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(plaintext: str) -> str:
    """Encrypt a token or secret value."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a previously encrypted token."""
    f = _get_fernet()
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except InvalidToken as e:
        raise ValueError("Failed to decrypt token -- invalid key or corrupted data") from e
