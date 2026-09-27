"""
BeautyCRM — Security Module
AES-256 encryption for bot tokens, JWT for authentication, password hashing.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# ============================================================
# Password Hashing
# ============================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================
# JWT Tokens
# ============================================================


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data (must include 'sub' — tenant_id or user identifier).
        expires_delta: Custom expiration time.
    
    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token: Encoded JWT string.
    
    Returns:
        Decoded payload dict.
    
    Raises:
        JWTError: If token is invalid or expired.
    """
    return jwt.decode(
        token, settings.secret_key, algorithms=[settings.jwt_algorithm]
    )


# ============================================================
# AES-256 Encryption (for Telegram Bot Tokens)
# ============================================================

def _get_aes_key() -> bytes:
    """Derive 32-byte AES key from the configured encryption key."""
    key_bytes = bytes.fromhex(settings.encryption_key)
    if len(key_bytes) != 32:
        # If not exactly 32 bytes, hash it to get a consistent 32-byte key
        key_bytes = hashlib.sha256(settings.encryption_key.encode()).digest()
    return key_bytes


def encrypt_token(plaintext: str) -> str:
    """
    Encrypt a plaintext string using AES-256-CBC.
    
    Returns:
        Hex-encoded string in format: iv_hex:ciphertext_hex
    """
    key = _get_aes_key()
    iv = secrets.token_bytes(16)
    
    # PKCS7 padding
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode()) + padder.finalize()
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    return f"{iv.hex()}:{ciphertext.hex()}"


def decrypt_token(encrypted: str) -> str:
    """
    Decrypt an AES-256-CBC encrypted string.
    
    Args:
        encrypted: Hex-encoded string in format: iv_hex:ciphertext_hex
    
    Returns:
        Decrypted plaintext string.
    """
    key = _get_aes_key()
    iv_hex, ciphertext_hex = encrypted.split(":")
    iv = bytes.fromhex(iv_hex)
    ciphertext = bytes.fromhex(ciphertext_hex)
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Remove PKCS7 padding
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    
    return data.decode()


# ============================================================
# Telegram initData Validation (for TWA)
# ============================================================

def validate_telegram_init_data(init_data: str, bot_token: str) -> Optional[dict]:
    """
    Validate Telegram Mini App initData using HMAC-SHA256.
    
    See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    
    Args:
        init_data: Raw initData string from TWA.
        bot_token: The bot's token.
    
    Returns:
        Parsed user data dict if valid, None otherwise.
    """
    import urllib.parse
    
    parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    
    if not received_hash:
        return None
    
    # Sort and create data-check string
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )
    
    # Create secret key: HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()
    
    # Calculate hash
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(calculated_hash, received_hash):
        return None
    
    # Parse user JSON
    import json
    user_data = parsed.get("user")
    if user_data:
        parsed["user"] = json.loads(user_data)
    
    return parsed


def generate_bot_token_hash(bot_token: str) -> str:
    """
    Generate a URL-safe hash from a bot token for webhook URLs.
    This avoids exposing the actual token in the URL.
    """
    return hashlib.sha256(bot_token.encode()).hexdigest()[:32]
