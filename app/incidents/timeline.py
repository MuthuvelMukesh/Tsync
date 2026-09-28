"""
Timeline service managing chronological progression of events within an incident.
"""

from datetime import datetime, timezone
from typing import List
from app.domain.incidents import TimelineEntry
from app.domain.messages import Message


class TimelineService:
    """Creates, orders, and formats timeline events for an incident."""

    @staticmethod
    def create_timeline_entry(
        incident_id: int, message: Message, content_override: str = ""
    ) -> TimelineEntry:
        content = content_override or message.headline or (message.cleaned_text[:180] + "...")
        is_major = message.importance_score >= 7.5 or message.is_breaking

        return TimelineEntry(
            id=None,
            incident_id=incident_id,
            timestamp=message.published_at or datetime.now(timezone.utc),
            content=content,
            source_channel=message.source_channel,
            importance_score=message.importance_score,
            is_major_event=is_major,
            message_id=message.id,
        )

    @staticmethod
    def get_chronological_timeline(entries: List[TimelineEntry]) -> List[TimelineEntry]:
        """Return timeline entries sorted chronologically."""
        return sorted(entries, key=lambda e: e.timestamp)
