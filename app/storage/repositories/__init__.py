"""
Repositories package for persistence abstractions and implementations.
"""

from app.storage.repositories.messages import (
    MessageRepository,
    SQLAlchemyMessageRepository,
)
from app.storage.repositories.incidents import (
    IncidentRepository,
    SQLAlchemyIncidentRepository,
)
from app.storage.repositories.sources import (
    SourceRepository,
    SQLAlchemySourceRepository,
)
from app.storage.repositories.entities import (
    EntityRepository,
    SQLAlchemyEntityRepository,
)
from app.storage.repositories.notifications import (
    NotificationAuditRepository,
    SQLAlchemyNotificationAuditRepository,
)

__all__ = [
    "MessageRepository",
    "SQLAlchemyMessageRepository",
    "IncidentRepository",
    "SQLAlchemyIncidentRepository",
    "SourceRepository",
    "SQLAlchemySourceRepository",
    "EntityRepository",
    "SQLAlchemyEntityRepository",
    "NotificationAuditRepository",
    "SQLAlchemyNotificationAuditRepository",
]
