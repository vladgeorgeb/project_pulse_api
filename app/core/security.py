from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import get_settings

settings = get_settings()

PASSWORD_HASH_NAME = "pbkdf2_sha256"
PASSWORD_HASH_DIGEST = "sha256"
PASSWORD_SALT_BYTES = 16
PASSWORD_HASH_ITERATIONS = 200_000
TOKEN_SIGN_DIGEST = "sha256"
TOKEN_SEPARATOR = "."


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        PASSWORD_HASH_DIGEST,
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return (
        f"{PASSWORD_HASH_NAME}${PASSWORD_HASH_ITERATIONS}$"
        f"{base64.urlsafe_b64encode(salt).decode('ascii')}$"
        f"{base64.urlsafe_b64encode(derived).decode('ascii')}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_str, salt_b64, digest_b64 = stored_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != PASSWORD_HASH_NAME:
        return False

    try:
        iterations = int(iterations_str)
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
    except (binascii.Error, UnicodeEncodeError, ValueError):
        return False

    actual = hashlib.pbkdf2_hmac(
        TOKEN_SIGN_DIGEST,
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual, expected)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire_at = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    header = {
        "alg": settings.jwt_algorithm,
        "typ": "JWT",
    }
    payload = {
        "sub": subject,
        "exp": int(expire_at.timestamp()),
    }
    header_bytes = json.dumps(
        header,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    payload_bytes = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    header_part = _b64url_encode(header_bytes)
    payload_part = _b64url_encode(payload_bytes)
    signing_input = f"{header_part}.{payload_part}"
    signature = hmac.new(
        settings.secret_key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    signature_part = _b64url_encode(signature)
    return f"{signing_input}{TOKEN_SEPARATOR}{signature_part}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature_part = token.split(".", 2)
    except ValueError as exc:
        raise ValueError("Invalid token format.") from exc

    signing_input = f"{header_part}.{payload_part}"
    expected_signature = hmac.new(
        settings.secret_key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()

    try:
        provided_signature = _b64url_decode(signature_part)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid token signature.") from exc

    if not hmac.compare_digest(expected_signature, provided_signature):
        raise ValueError("Invalid token signature.")

    try:
        header = json.loads(_b64url_decode(header_part).decode("utf-8"))
        payload = json.loads(_b64url_decode(payload_part).decode("utf-8"))
    except (
        binascii.Error,
        json.JSONDecodeError,
        UnicodeDecodeError,
        ValueError,
    ) as exc:
        raise ValueError("Invalid token payload.") from exc

    if not isinstance(header, dict):
        raise ValueError("Invalid token header.")
    if header.get("alg") != settings.jwt_algorithm or header.get("typ") != "JWT":
        raise ValueError("Invalid token header.")
    if not isinstance(payload, dict):
        raise ValueError("Invalid token payload.")

    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise ValueError("Invalid token payload.")

    if datetime.now(UTC).timestamp() >= exp:
        raise ValueError("Token expired.")

    return payload
