"""
Unit tests for timeline service.
"""

from datetime import datetime, timezone
from app.domain.messages import Message
from app.incidents.timeline import TimelineService


def test_timeline_entry_creation():
    now = datetime.now(timezone.utc)
    msg = Message(
        id=5,
        external_id="ext-5",
        source_channel="reuters",
        text="Emergency summit convened in Geneva.",
        cleaned_text="Emergency summit convened in Geneva.",
        published_at=now,
        importance_score=8.0,
        headline="Geneva Emergency Summit",
    )

    entry = TimelineService.create_timeline_entry(incident_id=1, message=msg)
    assert entry.incident_id == 1
    assert entry.is_major_event
    assert entry.content == "Geneva Emergency Summit"
    assert entry.source_channel == "reuters"
