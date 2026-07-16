from __future__ import annotations

from app.scheduler.registry import job_registry
from app.scheduler.scheduler import register_jobs, scheduler


def test_register_jobs_populates_registry():
    job_registry._jobs.clear()
    register_jobs()

    ids = {j.id for j in job_registry.all()}
    assert ids == {"refresh_dexscreener", "refresh_geckoterminal", "compute_alpha_scores", "scan_top_tokens_for_whale_activity"}


def test_register_jobs_adds_apscheduler_jobs():
    job_registry._jobs.clear()
    for job_id in ["refresh_dexscreener", "refresh_geckoterminal", "compute_alpha_scores"]:
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

    register_jobs()

    assert scheduler.get_job("refresh_dexscreener") is not None
    assert scheduler.get_job("compute_alpha_scores") is not None