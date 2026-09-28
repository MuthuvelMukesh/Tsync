"""
Domain model for incidents and their lifecycles.
Independent of databases, frameworks, and third-party APIs.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from app.domain.entities import NamedEntity
from app.domain.claims import Claim


class IncidentStatus(str, Enum):
    NEW = "NEW"
    DEVELOPING = "DEVELOPING"
    MONITORING = "MONITORING"
    RESOLVED = "RESOLVED"
    ARCHIVED = "ARCHIVED"


class IncidentSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class TimelineEntry:
    """A chronologically ordered event or update in an incident's progression."""
    id: Optional[int]
    incident_id: Optional[int]
    timestamp: datetime
    content: str
    source_channel: str
    importance_score: float = 0.0
    is_major_event: bool = False
    message_id: Optional[int] = None


@dataclass
class Incident:
    """Core domain entity representing an unfolding intelligence incident."""
    id: Optional[int]
    title: str
    category: str
    status: IncidentStatus = IncidentStatus.NEW
    severity: IncidentSeverity = IncidentSeverity.LOW
    importance_score: float = 0.0
    confidence_score: float = 0.5
    summary: str = ""
    why_it_matters: str = ""
    sources: list[str] = field(default_factory=list)
    entities: list[NamedEntity] = field(default_factory=list)
    timeline: list[TimelineEntry] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    contradictions_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    # Allowed state transitions according to lifecycle rules
    _TRANSITIONS = {
        IncidentStatus.NEW: {IncidentStatus.DEVELOPING, IncidentStatus.MONITORING, IncidentStatus.ARCHIVED},
        IncidentStatus.DEVELOPING: {IncidentStatus.MONITORING, IncidentStatus.RESOLVED, IncidentStatus.ARCHIVED},
        IncidentStatus.MONITORING: {IncidentStatus.DEVELOPING, IncidentStatus.RESOLVED, IncidentStatus.ARCHIVED},
        IncidentStatus.RESOLVED: {IncidentStatus.DEVELOPING, IncidentStatus.ARCHIVED},
        IncidentStatus.ARCHIVED: {IncidentStatus.DEVELOPING, IncidentStatus.MONITORING},
    }

    def can_transition_to(self, new_status: IncidentStatus) -> bool:
        """Verify if transition is valid under domain lifecycle rules."""
        if new_status == self.status:
            return True
        return new_status in self._TRANSITIONS.get(self.status, set())

    def transition_to(self, new_status: IncidentStatus, reason: str = "") -> None:
        """Perform lifecycle transition with validation."""
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Invalid incident state transition from {self.status.value} to {new_status.value} ({reason})"
            )
        self.status = new_status
        now = datetime.now(timezone.utc)
        self.updated_at = now
        if new_status == IncidentStatus.RESOLVED and not self.resolved_at:
            self.resolved_at = now

    def add_source(self, source: str) -> bool:
        """Add source channel if not already recorded."""
        if source and source not in self.sources:
            self.sources.append(source)
            return True
        return False

    def add_timeline_entry(self, entry: TimelineEntry) -> None:
        """Append timeline entry and keep timeline sorted chronologically."""
        self.timeline.append(entry)
        self.timeline.sort(
            key=lambda e: (
                e.timestamp.replace(tzinfo=timezone.utc)
                if e.timestamp and e.timestamp.tzinfo is None
                else (e.timestamp or datetime.min.replace(tzinfo=timezone.utc))
            )
        )
        self.updated_at = datetime.now(timezone.utc)

    def recompute_severity(self) -> None:
        """Derive severity category from current importance score."""
        if self.importance_score >= 8.5:
            self.severity = IncidentSeverity.CRITICAL
        elif self.importance_score >= 7.0:
            self.severity = IncidentSeverity.HIGH
        elif self.importance_score >= 4.5:
            self.severity = IncidentSeverity.MEDIUM
        else:
            self.severity = IncidentSeverity.LOW

    @property
    def is_breaking(self) -> bool:
        return self.importance_score >= 8.5 or self.severity == IncidentSeverity.CRITICAL

    @property
    def source_diversity_count(self) -> int:
        return len(set(self.sources))
