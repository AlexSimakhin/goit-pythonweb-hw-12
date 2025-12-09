"""Unit tests for auth utilities: hashing, verification, token create/decode."""
from datetime import timedelta

from app.utils.auth import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hash_and_verify():
    """Password hashing should verify correct password and reject incorrect one."""
    password = "securepass"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrongpass", hashed)


def test_create_and_decode_access_token():
    """Access token should decode back to original payload."""
    data = {"user_id": 123, "email": "test@example.com"}
    token = create_access_token(data, expires_delta=timedelta(minutes=5))
    payload = decode_access_token(token)
    assert payload["user_id"] == 123
    assert payload["email"] == "test@example.com"


def test_decode_access_token_invalid():
    """Invalid token decode should return None."""
    assert decode_access_token("invalid.token") is None
