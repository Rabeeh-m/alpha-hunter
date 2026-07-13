"""
Load test for the token screener's most common query pattern.

Run against a server with real ingested data (run `alpha-hunter ingest`
a few times first, or let the scheduler run for a while) -- testing
against an empty table tells you nothing about query performance under
realistic row counts.
"""

from __future__ import annotations

import random

from locust import HttpUser, between, task

CHAINS = ["ethereum", "base", "solana", "bnb_chain", "arbitrum", "polygon", "avalanche", "optimism"]
SORT_FIELDS = ["-liquidity_usd", "-volume_24h_usd", "-alpha_score", "-created_at"]


class ScreenerUser(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def list_tokens_default(self) -> None:
        """The most common request: no filters, default sort -- what the
        Screener page sends on first load."""
        self.client.get("/api/v1/tokens", name="/api/v1/tokens [default]")

    @task(3)
    def list_tokens_filtered(self) -> None:
        self.client.get(
            "/api/v1/tokens",
            params={"chain": random.choice(CHAINS), "sort": random.choice(SORT_FIELDS)},
            name="/api/v1/tokens [filtered+sorted]",
        )

    @task(2)
    def search_tokens(self) -> None:
        self.client.get(
            "/api/v1/tokens", params={"search": "a"}, name="/api/v1/tokens [search]"
        )

    @task(1)
    def health_check(self) -> None:
        self.client.get("/health", name="/health")