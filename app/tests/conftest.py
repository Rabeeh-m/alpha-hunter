import pytest
from app.core.database.session import get_engine

@pytest.fixture(scope="session", autouse=True)
async def _dispose_engine_at_session_end():
    """Cleanly closes all pooled connections before the shared event loop
    (see pyproject.toml: asyncio_default_fixture_loop_scope='session')
    is torn down. Without this, connections get garbage-collected after
    their loop is already closed, producing 'Event loop is closed'
    RuntimeWarnings at teardown."""
    yield
    await engine.dispose()
    
@pytest.fixture(scope="session", autouse=True)
async def dispose_engine():
    """Dispose the global async engine after the test session.

    This ensures that all connections are properly closed before the event loop
    shuts down, preventing ``RuntimeError: Event loop is closed`` errors.
    """
    yield
    engine = get_engine()
    await engine.dispose()


