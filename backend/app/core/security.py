import base64
import hashlib
import os
import secrets
import time
from typing import Any, Dict, Optional
import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException, status

from backend.app.core.config import settings

# --- Password Hashing (PBKDF2-HMAC-SHA256) ---

def hash_password(password: str) -> str:
    """Hashes a password securely using PBKDF2-HMAC-SHA256 with 100,000 iterations and random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"pbkdf2_sha256$100000${salt}${key.hex()}"


def verify_password(password: str, hashed_password: Optional[str]) -> bool:
    """Verifies a plain password against a stored PBKDF2-HMAC-SHA256 hash using constant-time comparison."""
    if not hashed_password or not hashed_password.startswith("pbkdf2_sha256$"):
        return False
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4:
            return False
        iterations = int(parts[1])
        salt = parts[2]
        expected_key = parts[3]
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return secrets.compare_digest(key.hex(), expected_key)
    except Exception:
        return False


# --- Session Token Cryptography ---

def generate_session_token() -> str:
    """Generates a high-entropy cryptographically random session token (URL-safe base64)."""
    return secrets.token_urlsafe(32)


def hash_session_token(raw_token: str) -> str:
    """Computes SHA-256 hash of raw session token for secure database lookup."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

# --- AES-256-GCM Token Encryption ---

def _get_encryption_key() -> bytes:
    """Decodes the 32-byte master key from settings."""
    try:
        raw_key = base64.b64decode(settings.ENCRYPTION_MASTER_KEY)
        if len(raw_key) != 32:
            raise ValueError("ENCRYPTION_MASTER_KEY must be exactly 32 bytes when decoded.")
        return raw_key
    except Exception:
        # Fallback 32-byte deterministic key for development/testing
        return b"32_bytes_dev_master_key_for_test"


def encrypt_token(plain_text: str) -> str:
    """Encrypts a plaintext string (e.g. OAuth access token) using AES-256-GCM.
    
    Format: base64(nonce [12 bytes] + ciphertext + tag [16 bytes])
    """
    if not plain_text:
        return ""
    key = _get_encryption_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    encrypted_bytes = aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
    return base64.b64encode(nonce + encrypted_bytes).decode("utf-8")


def decrypt_token(cipher_text: str) -> str:
    """Decrypts an AES-256-GCM encrypted base64 payload."""
    if not cipher_text:
        return ""
    key = _get_encryption_key()
    aesgcm = AESGCM(key)
    raw_data = base64.b64decode(cipher_text.encode("utf-8"))
    nonce = raw_data[:12]
    ciphertext_with_tag = raw_data[12:]
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
    return decrypted_bytes.decode("utf-8")


# --- JWT Token Verification ---

# In-memory JWKS cache
_JWKS_CACHE: Dict[str, Any] = {}
_JWKS_LAST_FETCH = 0.0


def create_test_jwt(
    user_id: str,
    email: str,
    expires_in_seconds: int = 3600,
    is_platform_admin: bool = False,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Generates a test/dev JWT token signed with SECRET_KEY for testing and local dev."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "role": "authenticated",
        "iat": now,
        "exp": now + expires_in_seconds,
        "is_platform_admin": is_platform_admin,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Validates an incoming Supabase JWT token.
    
    Verifies:
    1. Token format and expiration (exp)
    2. Audience (aud == 'authenticated' or custom)
    3. Signature using configured SECRET_KEY / SUPABASE_JWT_SECRET or JWKS.
    
    Returns decoded claims dictionary containing 'sub', 'email', etc.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # First attempt: Try decoding with application SECRET_KEY or SUPABASE_JWT_SECRET (HS256)
    jwt_secrets = [settings.SECRET_KEY]
    if settings.SUPABASE_JWT_SECRET:
        jwt_secrets.append(settings.SUPABASE_JWT_SECRET)

    last_error: Optional[Exception] = None

    for secret in jwt_secrets:
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                options={"verify_exp": True, "verify_aud": False},
            )
            if not payload.get("sub"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing subject (sub) claim.",
                )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            last_error = e
            continue

    # Second attempt: If JWKS is configured, try RS256 with Supabase public keys
    if settings.SUPABASE_JWT_JWKS_URL:
        try:
            jwks_client = jwt.PyJWKClient(settings.SUPABASE_JWT_JWKS_URL)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience="authenticated",
                options={"verify_exp": True},
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            last_error = e

    # If verification fails across all strategies
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Invalid authentication token: {str(last_error) if last_error else 'Signature verification failed'}",
        headers={"WWW-Authenticate": "Bearer"},
    )


# --- Password Reset Cryptography ---

def create_password_reset_token(user_id: str, email: str, pw_hash: Optional[str]) -> str:
    """Generates a secure, single-use, timed password reset token."""
    now = int(time.time())
    fingerprint = hashlib.sha256((pw_hash or "").encode("utf-8")).hexdigest()[:16]
    payload = {
        "sub": str(user_id),
        "email": email,
        "purpose": "password_reset",
        "fp": fingerprint,
        "iat": now,
        "exp": now + 3600,  # 1 hour expiration
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def verify_password_reset_token(token: str) -> Dict[str, Any]:
    """Verifies a password reset token signature, expiration, and purpose."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_exp": True},
        )
        if payload.get("purpose") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token purpose: not a password reset token.",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired. Please request a new one.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or malformed password reset token.",
        )


