"""
Source repository protocol and SQLAlchemy implementation.
Manages ingestion sources (Telegram channels, RSS feeds, etc.).
"""

from datetime import datetime, timezone
from typing import List, Optional, Protocol
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.storage.models import SourceModel


class SourceRepository(Protocol):
    """Abstract interface for managing data sources."""

    async def list_active(self) -> List[str]:
        ...

    async def add_source(self, username_or_id: str, title: str = "", source_type: str = "telegram") -> bool:
        ...

    async def remove_source(self, username_or_id: str) -> bool:
        ...

    async def mark_polled(self, username_or_id: str) -> None:
        ...


class SQLAlchemySourceRepository:
    """SQLAlchemy implementation of SourceRepository."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def list_active(self) -> List[str]:
        async with self._session_factory() as session:
            stmt = select(SourceModel.username_or_id).where(SourceModel.is_active == True)  # noqa: E712
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add_source(
        self, username_or_id: str, title: str = "", source_type: str = "telegram"
    ) -> bool:
        clean = username_or_id.strip().lstrip("@")
        async with self._session_factory() as session:
            async with session.begin():
                stmt = select(SourceModel).where(SourceModel.username_or_id == clean)
                existing = (await session.execute(stmt)).scalar_one_or_none()
                if existing:
                    if not existing.is_active:
                        existing.is_active = True
                        return True
                    return False
                model = SourceModel(
                    username_or_id=clean,
                    title=title or clean,
                    source_type=source_type,
                    is_active=True,
                )
                session.add(model)
                return True

    async def remove_source(self, username_or_id: str) -> bool:
        clean = username_or_id.strip().lstrip("@")
        async with self._session_factory() as session:
            async with session.begin():
                stmt = select(SourceModel).where(SourceModel.username_or_id == clean)
                existing = (await session.execute(stmt)).scalar_one_or_none()
                if existing:
                    existing.is_active = False
                    return True
                return False

    async def mark_polled(self, username_or_id: str) -> None:
        clean = username_or_id.strip().lstrip("@")
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            async with session.begin():
                stmt = (
                    update(SourceModel)
                    .where(SourceModel.username_or_id == clean)
                    .values(last_polled_at=now)
                )
                await session.execute(stmt)
