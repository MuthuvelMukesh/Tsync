"""
Unit tests for incident updater.
"""

from datetime import datetime, timezone
from app.domain.incidents import Incident, IncidentStatus, IncidentSeverity
from app.domain.messages import Message
from app.incidents.updater import IncidentUpdater


def test_updater_material_change_detection():
    updater = IncidentUpdater()
    now = datetime.now(timezone.utc)

    inc = Incident(
        id=1,
        title="Test Incident",
        category="technology",
        status=IncidentStatus.NEW,
        importance_score=5.0,
        sources=["source_1"],
    )

    msg = Message(
        id=2,
        external_id="2",
        source_channel="source_2",
        text="Corroboration from new source",
        cleaned_text="Corroboration from new source",
        published_at=now,
        importance_score=7.8,
    )

    updated_inc, is_material, reason = updater.update_incident(inc, msg)

    assert is_material
    assert "Corroborated by new source @source_2" in reason
    assert updated_inc.status == IncidentStatus.DEVELOPING
    assert updated_inc.importance_score == 7.8
    assert updated_inc.severity == IncidentSeverity.HIGH
