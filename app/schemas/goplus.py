from __future__ import annotations

from pydantic import BaseModel, Field


class GoPlusTokenSecurity(BaseModel):
    """Raw GoPlus response fields. GoPlus returns booleans as string
    "1"/"0" and numeric values as strings -- not our design choice, just
    faithfully modeling their actual API contract. Field AVAILABILITY
    varies by chain; every field here is Optional for that reason, not
    because the schema is being lazy about validation."""

    is_open_source: str | None = None
    is_proxy: str | None = None
    is_mintable: str | None = None
    owner_address: str | None = None
    can_take_back_ownership: str | None = None
    hidden_owner: str | None = None
    selfdestruct: str | None = None
    external_call: str | None = None
    buy_tax: str | None = None
    sell_tax: str | None = None
    is_honeypot: str | None = None
    transfer_pausable: str | None = None
    is_blacklisted: str | None = None
    is_whitelisted: str | None = None
    is_anti_whale: str | None = None
    trading_cooldown: str | None = None
    holder_count: str | None = None


class GoPlusResponse(BaseModel):
    code: int
    message: str
    result: dict[str, GoPlusTokenSecurity] = Field(default_factory=dict)