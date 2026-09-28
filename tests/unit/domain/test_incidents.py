"""
Unit tests for domain incident lifecycle and transitions.
"""

from datetime import datetime, timezone
import pytest

from app.domain.incidents import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    TimelineEntry,
)


def test_incident_lifecycle_valid_transitions():
    inc = Incident(
        id=1,
        title="Test Incident",
        category="technology",
        status=IncidentStatus.NEW,
    )
    assert inc.can_transition_to(IncidentStatus.DEVELOPING)

    inc.transition_to(IncidentStatus.DEVELOPING, "New corroborating reports")
    assert inc.status == IncidentStatus.DEVELOPING

    inc.transition_to(IncidentStatus.MONITORING)
    assert inc.status == IncidentStatus.MONITORING

    inc.transition_to(IncidentStatus.RESOLVED)
    assert inc.status == IncidentStatus.RESOLVED
    assert inc.resolved_at is not None


def test_incident_lifecycle_invalid_transition():
    inc = Incident(
        id=1,
        title="Test Incident",
        category="technology",
        status=IncidentStatus.NEW,
    )
    with pytest.raises(ValueError, match="Invalid incident state transition"):
        inc.transition_to(IncidentStatus.RESOLVED)


def test_incident_severity_recomputation():
    inc = Incident(id=1, title="Test", category="finance", importance_score=3.0)
    inc.recompute_severity()
    assert inc.severity == IncidentSeverity.LOW

    inc.importance_score = 5.0
    inc.recompute_severity()
    assert inc.severity == IncidentSeverity.MEDIUM

    inc.importance_score = 7.5
    inc.recompute_severity()
    assert inc.severity == IncidentSeverity.HIGH

    inc.importance_score = 9.2
    inc.recompute_severity()
    assert inc.severity == IncidentSeverity.CRITICAL
    assert inc.is_breaking


def test_timeline_sorting():
    t1 = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc)
    entry1 = TimelineEntry(id=1, incident_id=1, timestamp=t2, content="Second event", source_channel="b")
    entry2 = TimelineEntry(id=2, incident_id=1, timestamp=t1, content="First event", source_channel="a")

    inc = Incident(id=1, title="T", category="c")
    inc.add_timeline_entry(entry1)
    inc.add_timeline_entry(entry2)

    assert inc.timeline[0].content == "First event"
    assert inc.timeline[1].content == "Second event"
