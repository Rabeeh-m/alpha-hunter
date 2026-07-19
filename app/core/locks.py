from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from app.core.cache import get_redis
from app.core.exceptions import JobAlreadyRunning
from app.core.logging import get_logger

log = get_logger(__name__)

# Atomic "release only if I still own the lock" -- without this check, a
# slow job whose lock TTL expired mid-run could have its lock stolen and
# then accidentally released by a newer execution that isn't finished yet.
_RELEASE_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


@asynccontextmanager
async def job_lock(job_id: str, ttl_seconds: int = 300) -> AsyncGenerator[None]:
    """Prevents the same job from running concurrently -- either two
    overlapping intervals on one process, or the same job firing on two
    separate scheduler processes in a multi-instance deployment."""
    lock_key = f"lock:job:{job_id}"
    token = str(uuid.uuid4())
    redis = get_redis()

    acquired = await redis.set(lock_key, token, nx=True, ex=ttl_seconds)
    if not acquired:
        raise JobAlreadyRunning(f"Job '{job_id}' is already running", details={"job_id": job_id})

    log.debug("job_lock_acquired", job_id=job_id)
    try:
        yield
    finally:
        await redis.eval(_RELEASE_SCRIPT, 1, lock_key, token)
        log.debug("job_lock_released", job_id=job_id)
