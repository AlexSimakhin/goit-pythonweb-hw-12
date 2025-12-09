"""
Simple Redis cache utilities for storing and retrieving current user data.
"""
import os
import json
from typing import Optional

import redis
from redis.exceptions import RedisError

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Lazy singleton for Redis client without using `global` reassignment
def _client_singleton():
    client: Optional[redis.Redis] = None

    def get() -> redis.Redis:
        nonlocal client
        if client is None:
            client = redis.from_url(REDIS_URL, decode_responses=True)
        return client

    return get

_get_client = _client_singleton()

def get_client() -> redis.Redis:
    """Return a cached Redis client instance."""
    return _get_client()


def cache_user(user_id: int, data: dict, ttl_seconds: int = 1800) -> None:
    """Cache a user's data in Redis.

    Args:
        user_id: The user's primary key.
        data: A JSON-serializable dictionary of user data to cache.
        ttl_seconds: Time-to-live in seconds (default 1800 = 30 minutes).
    """
    client = get_client()
    key = f"user:{user_id}"
    client.setex(key, ttl_seconds, json.dumps(data))


def get_cached_user(user_id: int) -> Optional[dict]:
    """Retrieve cached user data if available.

    Args:
        user_id: The user's primary key.

    Returns:
        The cached user data as a dictionary if present and valid, otherwise None.
    """
    client = get_client()
    key = f"user:{user_id}"
    val = client.get(key)
    if not val:
        return None
    try:
        return json.loads(val)
    except json.JSONDecodeError:
        return None


def delete_user_cache(user_id: int) -> None:
    """Remove a user's cache entry.

    Call this after sensitive changes (email, role, avatar) to avoid stale data.
    """
    client = get_client()
    key = f"user:{user_id}"
    try:
        client.delete(key)
    except RedisError:
        # Best-effort; ignore deletion errors
        pass


def update_user_cache(user_id: int, data: dict, ttl_seconds: int = 1800) -> None:
    """Convenience wrapper to update cache atomically."""
    cache_user(user_id, data, ttl_seconds)
