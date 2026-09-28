"""
Notification protocol, result types, and policy engine.
Separates notification delivery from business rules and dispatching.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol

from app.domain.events import (
    DomainEvent,
    IncidentCreated,
    IncidentUpdated,
    BreakingIncidentDetected,
)
from app.domain.incidents import Incident


class NotificationDeliveryError(Exception):
    """Raised when notification delivery fails."""
    pass


@dataclass
class NotificationResult:
    """Result of attempting to dispatch a notification."""
    success: bool
    channel: str
    recipient: str
    external_message_id: Optional[str] = None
    error: Optional[str] = None


class NotificationProvider(Protocol):
    """Abstract interface for external notification delivery systems."""

    @property
    def channel_name(self) -> str:
        """Name of the provider channel ('whatsapp', 'telegram', etc.)."""
        ...

    async def send(self, recipient: str, message: str) -> NotificationResult:
        """Deliver text message to recipient."""
        ...


class NotificationPolicy:
    """Evaluates business rules to decide whether an event warrants immediate notification."""

    def __init__(self, quiet_hours_start: int = 23, quiet_hours_end: int = 6):
        self.quiet_hours_start = quiet_hours_start
        self.quiet_hours_end = quiet_hours_end

    def is_quiet_hours(self, now: Optional[datetime] = None) -> bool:
        """Check if current time is within quiet hours."""
        if now is None:
            now = datetime.now()
        hour = now.hour
        if self.quiet_hours_start > self.quiet_hours_end:
            return hour >= self.quiet_hours_start or hour < self.quiet_hours_end
        return self.quiet_hours_start <= hour < self.quiet_hours_end

    def should_notify(self, event: DomainEvent) -> bool:
        """
        Policy decision logic:
        - Breaking incident: ALWAYS notify immediately, even during quiet hours.
        - Material update on critical incident: notify if not quiet hours.
        - New incident with high severity: notify if not quiet hours.
        - Routine updates: DO NOT notify (reserved for hourly digest).
        """
        # Breaking alert takes immediate priority over quiet hours
        if isinstance(event, BreakingIncidentDetected):
            return True

        # In quiet hours, suppress non-breaking notifications
        if self.is_quiet_hours():
            return False

        if isinstance(event, IncidentCreated):
            # Only immediately notify if high or critical severity
            return event.incident.importance_score >= 7.5

        if isinstance(event, IncidentUpdated):
            # Only notify if material change AND incident is high importance
            return event.is_material_change and event.incident.importance_score >= 7.0

        return False
