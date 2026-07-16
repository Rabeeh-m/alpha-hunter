from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.logging import get_logger
from app.scheduler.execution import execute_job
from app.scheduler.jobs import compute_alpha_scores, refresh_dexscreener, refresh_geckoterminal, scan_top_tokens_for_whale_activity, scan_top_tokens_for_social_activity
from app.scheduler.registry import JobDefinition, job_registry

log = get_logger(__name__)

scheduler = AsyncIOScheduler()


def register_jobs() -> None:
    definitions = [
        JobDefinition(
            id="refresh_dexscreener",
            name="DexScreener Refresh",
            description="Fetch latest token profiles + pairs from DexScreener",
            category="collector",
            func=refresh_dexscreener,
            interval_seconds=90,
        ),
        JobDefinition(
            id="refresh_geckoterminal",
            name="GeckoTerminal Refresh",
            description="Fetch new pools across all supported GeckoTerminal networks",
            category="collector",
            func=refresh_geckoterminal,
            interval_seconds=90,
        ),
        JobDefinition(
            id="compute_alpha_scores",
            name="Alpha Score Ranking Pass",
            description="Recompute explainable alpha scores for all tokens",
            category="ranking",
            func=compute_alpha_scores,
            interval_seconds=120,  
        ),
        JobDefinition(
            id="scan_top_tokens_for_whale_activity",
            name="Whale Activity Scan (Top 10 Tokens)",
            description="Re-scan top-ranked tokens' holders to detect balance changes -- bounded scope, see docstring",
            category="whale-monitoring",
            func=scan_top_tokens_for_whale_activity,
            interval_seconds=1200,  # 20min -- balances rate-limit exposure against monitoring freshness
        ),
        JobDefinition(
            id="scan_top_tokens_for_social_activity",
            name="Social Activity Scan (Top 10 Tokens)",
            description="Scan top-ranked tokens' Telegram channels -- bounded scope, Twitter/X excluded (see docs)",
            category="social",
            func=scan_top_tokens_for_social_activity,
            interval_seconds=3600,  # 1h -- lower frequency than whale monitoring; scraping is heavier/slower per-call
        ),
    ]

    for job_def in definitions:
        job_registry.register(job_def)
        if job_def.enabled:
            scheduler.add_job(
                execute_job,
                trigger=IntervalTrigger(seconds=job_def.interval_seconds),
                args=[job_def],
                id=job_def.id,
                max_instances=1,
                replace_existing=True,
            )

def start_scheduler() -> None:
    register_jobs()
    scheduler.start()
    log.info("scheduler_started", job_count=len(job_registry.all()))


def shutdown_scheduler() -> None:
    scheduler.shutdown(wait=True)
    log.info("scheduler_shutdown")