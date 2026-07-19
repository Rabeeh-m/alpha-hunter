from __future__ import annotations

from unittest.mock import patch

from httpx import ASGITransport, AsyncClient

# Patch scheduler functions BEFORE app.main is imported to prevent the
# module-level `app = create_app()` from calling the real implementations.
_patcher_start = patch("app.main.start_scheduler")
_patcher_stop = patch("app.main.shutdown_scheduler")
_patcher_start.start()
_patcher_stop.start()

from app.main import create_app  # noqa: E402


def _make_app():
    return create_app()


def test_create_app_sets_title_and_version():
    app = _make_app()
    assert app.title == "Alpha Hunter"
    assert app.version == "0.1.0"


def test_create_app_has_routes():
    app = _make_app()
    route_paths = set()
    for r in app.routes:
        path = getattr(r, "path", None)
        if path:
            route_paths.add(path)
    assert "/health" in route_paths


async def test_lifespan_starts_and_stops_scheduler():
    with (
        patch("app.main.start_scheduler") as mock_start,
        patch("app.main.shutdown_scheduler") as mock_stop,
    ):
        app = _make_app()

        async with app.router.lifespan_context(app):
            mock_start.assert_called_once()
            mock_stop.assert_not_called()

        mock_stop.assert_called_once()


async def test_health_endpoint_returns_ok():
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "Alpha Hunter"}
