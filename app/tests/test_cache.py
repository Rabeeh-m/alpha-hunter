import asyncio

import pytest

from app.core.cache import get_redis


@pytest.mark.asyncio
async def test_get_redis_same_loop_returns_same_instance():
    redis1 = get_redis()
    redis2 = get_redis()
    assert redis1 is redis2


def test_get_redis_different_loops_returns_different_instances():
    redis_instances = []

    async def get_instance():
        redis_instances.append(get_redis())

    # Create first loop and run
    loop1 = asyncio.new_event_loop()
    try:
        loop1.run_until_complete(get_instance())
    finally:
        loop1.close()

    # Create second loop and run
    loop2 = asyncio.new_event_loop()
    try:
        loop2.run_until_complete(get_instance())
    finally:
        loop2.close()

    assert len(redis_instances) == 2
    assert redis_instances[0] is not redis_instances[1]


def test_get_redis_no_running_loop():
    # Calling get_redis outside an async loop should not raise an error
    # and should return a fallback Redis instance.
    redis = get_redis()
    assert redis is not None
