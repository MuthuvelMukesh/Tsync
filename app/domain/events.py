"""
Domain events and in-process event dispatcher.
Independent of databases, external brokers, and frameworks.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List, Type, TypeVar
import inspect

from app.domain.incidents import Incident, IncidentSeverity, IncidentStatus
from app.domain.claims import Contradiction


@dataclass
class DomainEvent:
    """Base class for all domain events."""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class IncidentCreated(DomainEvent):
    incident: Incident = field(default=None)  # type: ignore


@dataclass
class IncidentUpdated(DomainEvent):
    incident: Incident = field(default=None)  # type: ignore
    is_material_change: bool = False
    change_summary: str = ""
    previous_score: float = 0.0
    new_score: float = 0.0


@dataclass
class IncidentEscalated(DomainEvent):
    incident: Incident = field(default=None)  # type: ignore
    previous_severity: IncidentSeverity = IncidentSeverity.LOW
    new_severity: IncidentSeverity = IncidentSeverity.HIGH
    reason: str = ""


@dataclass
class IncidentResolved(DomainEvent):
    incident: Incident = field(default=None)  # type: ignore
    resolution_note: str = ""


@dataclass
class ContradictionDetected(DomainEvent):
    incident: Incident = field(default=None)  # type: ignore
    contradiction: Contradiction = field(default=None)  # type: ignore


@dataclass
class BreakingIncidentDetected(DomainEvent):
    incident: Incident = field(default=None)  # type: ignore
    trigger_message_text: str = ""


EventType = TypeVar("EventType", bound=DomainEvent)
EventHandler = Callable[[Any], Coroutine[Any, Any, None] | None]


class EventDispatcher:
    """
    Lightweight, in-process event dispatcher.
    Decouples domain mutations from notifications, audit logging, and adapters.
    """

    def __init__(self):
        self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}

    def subscribe(self, event_cls: Type[DomainEvent], handler: EventHandler) -> None:
        """Register a handler for a domain event type."""
        if event_cls not in self._handlers:
            self._handlers[event_cls] = []
        if handler not in self._handlers[event_cls]:
            self._handlers[event_cls].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        """Dispatch event to all subscribed handlers."""
        event_cls = type(event)
        # Also invoke handlers for parent classes if registered
        handlers: List[EventHandler] = []
        for registered_cls, registered_handlers in self._handlers.items():
            if issubclass(event_cls, registered_cls):
                handlers.extend(registered_handlers)

        for handler in handlers:
            try:
                res = handler(event)
                if inspect.isawaitable(res):
                    await res
            except Exception as e:
                # Log or handle dispatcher error without crashing the publisher
                print(f"[EVENT_DISPATCHER] Error in handler {handler}: {e}")
