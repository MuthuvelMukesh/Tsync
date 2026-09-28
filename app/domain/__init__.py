"""
Domain layer for Tsync.
Contains pure business logic, models, and domain events.
Free of external dependencies (databases, APIs, third-party libraries).
"""

from app.domain.entities import EntityType, NamedEntity
from app.domain.messages import Message, RawMessage, MessageFilterResult
from app.domain.claims import Claim, Contradiction
from app.domain.incidents import (
    Incident,
    IncidentStatus,
    IncidentSeverity,
    TimelineEntry,
)
from app.domain.events import (
    DomainEvent,
    IncidentCreated,
    IncidentUpdated,
    IncidentEscalated,
    IncidentResolved,
    ContradictionDetected,
    BreakingIncidentDetected,
    EventDispatcher,
)

__all__ = [
    "EntityType",
    "NamedEntity",
    "Message",
    "RawMessage",
    "MessageFilterResult",
    "Claim",
    "Contradiction",
    "Incident",
    "IncidentStatus",
    "IncidentSeverity",
    "TimelineEntry",
    "DomainEvent",
    "IncidentCreated",
    "IncidentUpdated",
    "IncidentEscalated",
    "IncidentResolved",
    "ContradictionDetected",
    "BreakingIncidentDetected",
    "EventDispatcher",
]
