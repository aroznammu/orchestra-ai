"""Token encryption with AES-256-GCM (preferred) and Fernet (legacy fallback).

AES-256-GCM provides authenticated encryption with a 256-bit key, 96-bit nonce,
and 128-bit auth tag. Fernet (AES-128-CBC + HMAC-SHA256) is retained for
backward compatibility with previously encrypted data.

Selection logic:
  - If ENCRYPTION_KEY is set (64-char hex = 32 bytes), use AES-256-GCM.
  - Otherwise fall back to FERNET_KEY.
"""

import os
import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from orchestra.config import get_settings

_AES_GCM_PREFIX = b"aes256gcm:"
_NONCE_SIZE = 12  # 96 bits per NIST recommendation

_cached_fernet: Fernet | None = None
_cached_aesgcm: AESGCM | None = None
_use_aesgcm: bool | None = None


def _init_crypto() -> None:
    global _cached_fernet, _cached_aesgcm, _use_aesgcm
    if _use_aesgcm is not None:
        return

    settings = get_settings()
    enc_key = settings.encryption_key.get_secret_value()

    if enc_key and not enc_key.startswith("CHANGE-ME"):
        try:
            raw = bytes.fromhex(enc_key) if len(enc_key) == 64 else enc_key.encode()[:32]
            if len(raw) != 32:
                raise ValueError("ENCRYPTION_KEY must be 32 bytes (64 hex chars) for AES-256-GCM")
            _cached_aesgcm = AESGCM(raw)
            _use_aesgcm = True
            return
        except (ValueError, TypeError):
            pass

    fernet_key = settings.fernet_key.get_secret_value()
    if fernet_key.startswith("CHANGE-ME"):
        fernet_key = Fernet.generate_key().decode()
    _cached_fernet = Fernet(fernet_key.encode() if isinstance(fernet_key, str) else fernet_key)
    _use_aesgcm = False


def encrypt_token(plaintext: str) -> str:
    """Encrypt a token or secret value. Uses AES-256-GCM if configured, else Fernet."""
    _init_crypto()
    if _use_aesgcm and _cached_aesgcm is not None:
        nonce = os.urandom(_NONCE_SIZE)
        ct = _cached_aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.urlsafe_b64encode(_AES_GCM_PREFIX + nonce + ct).decode()

    assert _cached_fernet is not None
    return _cached_fernet.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a previously encrypted token. Detects AES-256-GCM vs Fernet automatically."""
    _init_crypto()
    try:
        raw = base64.urlsafe_b64decode(ciphertext.encode())
        if raw.startswith(_AES_GCM_PREFIX):
            if _cached_aesgcm is None:
                raise ValueError("AES-256-GCM encrypted data but ENCRYPTION_KEY not configured")
            payload = raw[len(_AES_GCM_PREFIX):]
            nonce, ct = payload[:_NONCE_SIZE], payload[_NONCE_SIZE:]
            return _cached_aesgcm.decrypt(nonce, ct, None).decode()
    except (ValueError, Exception):
        pass

    if _cached_fernet is not None:
        try:
            return _cached_fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken as e:
            raise ValueError("Failed to decrypt token -- invalid key or corrupted data") from e

    raise ValueError("No valid decryption key configured")
