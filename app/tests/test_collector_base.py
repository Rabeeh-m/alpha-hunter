from __future__ import annotations

import asyncio

from app.collectors.base import TokenProvider
from app.schemas.token import TokenCreate


class _ConcreteProvider:
    name = "test-provider"

    async def fetch_latest_tokens(self) -> list[TokenCreate]:
        return []

    async def close(self) -> None:
        pass


class _MinimalProvider:
    name = "minimal"

    async def fetch_latest_tokens(self) -> list[TokenCreate]:
        return []


class TestTokenProviderProtocol:
    def test_concrete_class_has_required_attributes(self):
        provider = _ConcreteProvider()
        assert hasattr(provider, "name")
        assert hasattr(provider, "fetch_latest_tokens")

    def test_fetch_latest_tokens_returns_empty_list(self):
        provider = _ConcreteProvider()
        result = asyncio.run(provider.fetch_latest_tokens())
        assert result == []

    def test_close_is_callable_and_returns_none(self):
        provider = _ConcreteProvider()
        result = asyncio.run(provider.close())
        assert result is None

    def test_protocol_name_is_set(self):
        provider = _ConcreteProvider()
        assert provider.name == "test-provider"

    def test_minimal_provider_satisfies_protocol(self):
        provider = _MinimalProvider()
        assert hasattr(provider, "name")
        assert hasattr(provider, "fetch_latest_tokens")
        assert not hasattr(provider, "close")

    def test_minimal_provider_duck_types_as_token_provider(self):
        provider = _MinimalProvider()
        typed: TokenProvider = provider
        assert typed.name == "minimal"

    def test_concrete_provider_duck_types_as_token_provider(self):
        provider = _ConcreteProvider()
        typed: TokenProvider = provider
        assert typed.name == "test-provider"

    def test_fetch_returns_token_create_list(self):
        provider = _ConcreteProvider()
        result = asyncio.run(provider.fetch_latest_tokens())
        assert isinstance(result, list)

    def test_protocol_importable(self):
        assert TokenProvider is not None
