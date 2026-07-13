from __future__ import annotations

import uuid
from typing import Any


class AlphaHunterError(Exception):
    """Base for all domain errors. Carries enough structured context to
    both log usefully and let calling code decide programmatically
    whether to retry, without string-matching exception messages."""

    error_code: str = "ALPHA_HUNTER_ERROR"
    recoverable: bool = False

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.correlation_id = correlation_id or str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "correlation_id": self.correlation_id,
            "recoverable": self.recoverable,
        }


class ProviderUnavailable(AlphaHunterError):
    error_code = "PROVIDER_UNAVAILABLE"
    recoverable = True


class ProviderRateLimited(AlphaHunterError):
    error_code = "PROVIDER_RATE_LIMITED"
    recoverable = True


class CollectorTimeout(AlphaHunterError):
    error_code = "COLLECTOR_TIMEOUT"
    recoverable = True


class SchedulerError(AlphaHunterError):
    error_code = "SCHEDULER_ERROR"
    recoverable = False


class JobAlreadyRunning(AlphaHunterError):
    error_code = "JOB_ALREADY_RUNNING"
    recoverable = True


class CacheUnavailable(AlphaHunterError):
    error_code = "CACHE_UNAVAILABLE"
    recoverable = True


class RepositoryError(AlphaHunterError):
    error_code = "REPOSITORY_ERROR"
    recoverable = False


class ExternalAPIError(AlphaHunterError):
    error_code = "EXTERNAL_API_ERROR"
    recoverable = True

class InvalidSortField(AlphaHunterError):
    error_code = "INVALID_SORT_FIELD"
    recoverable = True