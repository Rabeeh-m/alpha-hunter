from __future__ import annotations

import pytest

from app.core.exceptions import JobAlreadyRunning
from app.core.locks import job_lock


async def test_job_lock_prevents_concurrent_execution():
    async with job_lock("concurrency-test-job"):
        with pytest.raises(JobAlreadyRunning):
            async with job_lock("concurrency-test-job"):
                pass  # pragma: no cover -- should never reach here


async def test_job_lock_releases_after_context_exit():
    async with job_lock("release-test-job"):
        pass

    # lock should be free again -- this should NOT raise
    async with job_lock("release-test-job"):
        pass