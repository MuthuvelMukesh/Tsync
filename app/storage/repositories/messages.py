"""
Message repository protocol and SQLAlchemy implementation.
Maps between domain Message entities and persistence models.
"""

from datetime import datetime, timezone
from typing import List, Optional, Protocol
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.messages import Message
from app.storage.models import MessageModel


class MessageRepository(Protocol):
    """Abstract interface for message persistence."""

    async def get(self, message_id: int) -> Optional[Message]:
        ...

    async def get_by_source_and_external_id(
        self, source_channel: str, external_id: str
    ) -> Optional[Message]:
        ...

    async def create(self, message: Message) -> Message:
        ...

    async def bulk_create(self, messages: List[Message]) -> List[Message]:
        ...

    async def update(self, message: Message) -> Message:
        ...

    async def get_unprocessed(self, limit: int = 100) -> List[Message]:
        ...

    async def get_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Message]:
        ...

    async def get_selected(self, start_date: Optional[datetime] = None) -> List[Message]:
        ...


class SQLAlchemyMessageRepository:
    """SQLAlchemy implementation of MessageRepository."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _to_domain(model: MessageModel) -> Message:
        return Message(
            id=model.id,
            external_id=model.external_id,
            source_channel=model.source_channel,
            text=model.text,
            cleaned_text=model.cleaned_text,
            published_at=model.published_at,
            category=model.category,
            importance_score=model.importance_score,
            is_selected=model.is_selected,
            headline=model.headline,
            summary=model.summary,
            why_it_matters=model.why_it_matters,
            incident_id=model.incident_id,
            created_at=model.created_at,
        )

    async def get(self, message_id: int) -> Optional[Message]:
        async with self._session_factory() as session:
            model = await session.get(MessageModel, message_id)
            return self._to_domain(model) if model else None

    async def get_by_source_and_external_id(
        self, source_channel: str, external_id: str
    ) -> Optional[Message]:
        async with self._session_factory() as session:
            stmt = select(MessageModel).where(
                MessageModel.source_channel == source_channel,
                MessageModel.external_id == external_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_domain(model) if model else None

    async def create(self, message: Message) -> Message:
        async with self._session_factory() as session:
            async with session.begin():
                model = MessageModel(
                    external_id=message.external_id,
                    source_channel=message.source_channel,
                    text=message.text,
                    cleaned_text=message.cleaned_text or message.text,
                    published_at=message.published_at,
                    category=message.category,
                    importance_score=message.importance_score,
                    is_selected=message.is_selected,
                    headline=message.headline,
                    summary=message.summary,
                    why_it_matters=message.why_it_matters,
                    incident_id=message.incident_id,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(model)
                await session.flush()
                message.id = model.id
                return self._to_domain(model)

    async def bulk_create(self, messages: List[Message]) -> List[Message]:
        if not messages:
            return []
        saved: List[Message] = []
        async with self._session_factory() as session:
            async with session.begin():
                for msg in messages:
                    # Check for existing duplicate
                    stmt = select(MessageModel).where(
                        MessageModel.source_channel == msg.source_channel,
                        MessageModel.external_id == msg.external_id,
                    )
                    existing = (await session.execute(stmt)).scalar_one_or_none()
                    if existing is None:
                        model = MessageModel(
                            external_id=msg.external_id,
                            source_channel=msg.source_channel,
                            text=msg.text,
                            cleaned_text=msg.cleaned_text or msg.text,
                            published_at=msg.published_at,
                            category=msg.category,
                            importance_score=msg.importance_score,
                            is_selected=msg.is_selected,
                            headline=msg.headline,
                            summary=msg.summary,
                            why_it_matters=msg.why_it_matters,
                            incident_id=msg.incident_id,
                            created_at=datetime.now(timezone.utc),
                        )
                        session.add(model)
                        await session.flush()
                        saved.append(self._to_domain(model))
                    else:
                        saved.append(self._to_domain(existing))
        return saved

    async def update(self, message: Message) -> Message:
        if message.id is None:
            raise ValueError("Cannot update message without an ID")
        async with self._session_factory() as session:
            async with session.begin():
                stmt = (
                    update(MessageModel)
                    .where(MessageModel.id == message.id)
                    .values(
                        category=message.category,
                        importance_score=message.importance_score,
                        is_selected=message.is_selected,
                        headline=message.headline,
                        summary=message.summary,
                        why_it_matters=message.why_it_matters,
                        incident_id=message.incident_id,
                    )
                )
                await session.execute(stmt)
                return message

    async def get_unprocessed(self, limit: int = 100) -> List[Message]:
        async with self._session_factory() as session:
            stmt = (
                select(MessageModel)
                .where(MessageModel.category == "uncategorized")
                .order_by(MessageModel.published_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def get_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Message]:
        async with self._session_factory() as session:
            stmt = (
                select(MessageModel)
                .where(
                    MessageModel.published_at >= start_date,
                    MessageModel.published_at <= end_date,
                )
                .order_by(MessageModel.importance_score.desc())
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def get_selected(self, start_date: Optional[datetime] = None) -> List[Message]:
        async with self._session_factory() as session:
            stmt = select(MessageModel).where(MessageModel.is_selected == True)  # noqa: E712
            if start_date:
                stmt = stmt.where(MessageModel.published_at >= start_date)
            stmt = stmt.order_by(MessageModel.importance_score.desc())
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]
