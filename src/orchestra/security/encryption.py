"""Token encryption using Fernet symmetric encryption."""

from cryptography.fernet import Fernet, InvalidToken

from orchestra.config import get_settings


_cached_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _cached_fernet
    if _cached_fernet is not None:
        return _cached_fernet
    settings = get_settings()
    key = settings.fernet_key.get_secret_value()
    if key.startswith("CHANGE-ME"):
        key = Fernet.generate_key().decode()
    _cached_fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _cached_fernet


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
