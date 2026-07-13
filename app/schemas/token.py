from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.models.chain import Chain
from decimal import Decimal

class TokenPage(BaseModel):
    items: list["TokenRead"]
    page: int
    page_size: int
    total: int
    total_pages: int

    model_config = {"from_attributes": True}

class TokenCreate(BaseModel):
    chain: Chain
    contract_address: str
    pair_address: str | None = None
    name: str
    symbol: str
    dex: str | None = None
    liquidity_usd: Decimal | None = None
    market_cap_usd: Decimal | None = None
    fdv_usd: Decimal | None = None
    volume_24h_usd: Decimal | None = None
    price_usd: Decimal | None = None

class TokenRead(BaseModel):
    id: UUID
    chain: Chain
    contract_address: str
    pair_address: str | None
    name: str
    symbol: str
    dex: str | None
    liquidity_usd: Decimal | None
    market_cap_usd: Decimal | None
    fdv_usd: Decimal | None
    volume_24h_usd: Decimal | None
    price_usd: Decimal | None
    holder_count: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
    
class TokenSnapshotRead(BaseModel):
    captured_at: datetime
    price_usd: Decimal | None
    liquidity_usd: Decimal | None
    volume_24h_usd: Decimal | None
    market_cap_usd: Decimal | None
    fdv_usd: Decimal | None

    model_config = {"from_attributes": True}