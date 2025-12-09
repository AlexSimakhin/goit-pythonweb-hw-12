"""Unit tests for Redis caching utilities and get_current_user behavior."""
import json
from unittest.mock import patch

from app.utils.cache import cache_user, delete_user_cache, get_cached_user
from app.utils import auth as auth_utils


class FakeRedis:
    """Minimal in-memory Redis client stub for unit tests."""

    def __init__(self):
        self.store = {}

    def setex(self, key, ttl_seconds, value):
        """Set a value with TTL (TTL ignored in tests)."""
        # Use ttl_seconds name to avoid unused-argument warning and document intent
        _ = ttl_seconds
        self.store[key] = value

    def get(self, key):
        """Get a value by key, returning None if absent."""
        return self.store.get(key)

    def delete(self, key):
        """Delete a key if present."""
        self.store.pop(key, None)


def test_cache_user_and_get_cached_user():
    """cache_user should persist data and get_cached_user should restore it."""
    fake = FakeRedis()
    with patch('app.utils.cache.get_client', return_value=fake):
        cache_user(1, {"id": 1, "username": "test", "email": "t@example.com", "role": "user"})
        cached = get_cached_user(1)
        assert cached is not None
        assert cached["username"] == "test"


def test_delete_user_cache():
    """delete_user_cache should remove cached entry."""
    fake = FakeRedis()
    with patch('app.utils.cache.get_client', return_value=fake):
        cache_user(2, {"id": 2, "username": "del", "email": "d@example.com", "role": "user"})
        assert get_cached_user(2) is not None
        delete_user_cache(2)
        assert get_cached_user(2) is None


def test_get_current_user_reads_from_cache():
    """get_current_user should return cached user when token matches cache."""
    token = auth_utils.create_access_token({"user_id": 3, "email": "c@example.com"})
    fake = FakeRedis()
    data = {"id": 3, "username": "cached", "email": "c@example.com", "role": "user"}
    fake.setex("user:3", 1800, json.dumps(data))
    with patch('app.utils.cache.get_client', return_value=fake):
        user = auth_utils.get_current_user(token)
        assert user is not None
        assert user["username"] == "cached"
