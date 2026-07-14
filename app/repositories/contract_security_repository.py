from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.contracts.risk_scoring import ContractRiskResult
from app.models.contract_security import ContractSecurity
from app.repositories.base import BaseRepository


class ContractSecurityRepository(BaseRepository[ContractSecurity]):
    model = ContractSecurity

    async def get_by_token_id(self, token_id: UUID) -> ContractSecurity | None:
        result = await self.session.execute(
            select(ContractSecurity).where(ContractSecurity.token_id == token_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, token_id: UUID, risk: ContractRiskResult) -> ContractSecurity:
        existing = await self.get_by_token_id(token_id)
        fields = {
            "safety_score": risk.safety_score, "flags": risk.flags,
            "is_honeypot": risk.is_honeypot, "is_mintable": risk.is_mintable,
            "is_open_source": risk.is_open_source, "buy_tax": risk.buy_tax,
            "sell_tax": risk.sell_tax, "owner_address": risk.owner_address,
        }
        if existing is not None:
            for key, value in fields.items():
                setattr(existing, key, value)
            await self.session.flush()
            return existing

        record = ContractSecurity(token_id=token_id, **fields)
        return await self.add(record)