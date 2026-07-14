from __future__ import annotations

from pydantic import BaseModel, Field


class EtherscanTransfer(BaseModel):
    from_address: str = Field(alias="from")
    to_address: str = Field(alias="to")
    value: str
    token_decimal: str | None = Field(default=None, alias="tokenDecimal")

    model_config = {"populate_by_name": True}
