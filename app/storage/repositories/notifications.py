"""
Notification audit repository protocol and SQLAlchemy implementation.
Records delivered notifications for audit and rate-limiting purposes.
"""

from datetime import datetime, timezone
from typing import List, Optional, Protocol
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.storage.models import NotificationAuditModel


class NotificationAuditRepository(Protocol):
    """Abstract interface for recording notification dispatches."""

    async def record(
        self,
        event_type: str,
        recipient: str,
        channel: str,
        message_payload: str,
        status: str = "sent",
        error: Optional[str] = None,
    ) -> None:
        ...

    async def get_recent(self, limit: int = 50) -> List[dict]:
        ...


class SQLAlchemyNotificationAuditRepository:
    """SQLAlchemy implementation of NotificationAuditRepository."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def record(
        self,
        event_type: str,
        recipient: str,
        channel: str,
        message_payload: str,
        status: str = "sent",
        error: Optional[str] = None,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                model = NotificationAuditModel(
                    event_type=event_type,
                    recipient=recipient,
                    channel=channel,
                    message_payload=message_payload,
                    status=status,
                    error=error,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(model)

    async def get_recent(self, limit: int = 50) -> List[dict]:
        async with self._session_factory() as session:
            stmt = (
                select(NotificationAuditModel)
                .order_by(NotificationAuditModel.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return [
                {
                    "id": m.id,
                    "event_type": m.event_type,
                    "recipient": m.recipient,
                    "channel": m.channel,
                    "status": m.status,
                    "error": m.error,
                    "created_at": m.created_at.isoformat(),
                }
                for m in result.scalars().all()
            ]
