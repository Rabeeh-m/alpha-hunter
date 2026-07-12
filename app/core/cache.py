from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis, from_url

from app.core.config import get_settings

settings = get_settings()
redis_client: Redis = from_url(str(settings.redis_url), decode_responses=True)


async def cache_get(key: str) -> Any | None:
    raw = await redis_client.get(key)
    return json.loads(raw) if raw else None


async def cache_set(key: str, value: Any, ttl_seconds: int = 60) -> None:
    await redis_client.set(key, json.dumps(value), ex=ttl_seconds)