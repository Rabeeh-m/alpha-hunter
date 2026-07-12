import asyncio
import json
import weakref
from typing import Any

from redis.asyncio import Redis, from_url

from app.core.config import get_settings

# Cache Redis client instances per event loop. Using a WeakKeyDictionary ensures
# that once an event loop is closed and garbage collected (e.g. at the end of a pytest test),
# the corresponding Redis client is cleaned up as well as its connection pool.
_redis_clients: weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, Redis] = weakref.WeakKeyDictionary()

def get_redis() -> Redis:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Fallback if called outside of a running asyncio event loop.
        # Create a one-off Redis client that is not bound to a stored thread-loop cache.
        settings = get_settings()
        return from_url(
            str(settings.redis_url),
            decode_responses=True,
        )

    if loop not in _redis_clients:
        settings = get_settings()
        _redis_clients[loop] = from_url(
            str(settings.redis_url),
            decode_responses=True,
        )
    return _redis_clients[loop]


async def cache_get(key: str):
    redis = get_redis()
    raw = await redis.get(key)
    return json.loads(raw) if raw else None


async def cache_set(
    key: str,
    value,
    ttl_seconds=60,
):
    redis = get_redis()
    await redis.set(
        key,
        json.dumps(value),
        ex=ttl_seconds,
    )