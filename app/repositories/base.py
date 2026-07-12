from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic CRUD repository. Services depend on this interface, never on
    raw SQLAlchemy sessions directly — that's what makes services testable
    without a real database.
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, id_: UUID) -> ModelT | None:
        return await self.session.get(self.model, id_)

    async def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[ModelT]:
        result = await self.session.execute(select(self.model).limit(limit).offset(offset))
        return list(result.scalars().all())
