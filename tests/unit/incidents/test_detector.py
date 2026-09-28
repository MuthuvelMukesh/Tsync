"""
Unit tests for incident detector.
"""

from datetime import datetime, timezone
from app.domain.messages import Message
from app.incidents.detector import IncidentDetector


def test_detector_identifies_incident():
    detector = IncidentDetector(min_incident_score=5.0)
    now = datetime.now(timezone.utc)

    high_msg = Message(1, "1", "c", "text", "text", now, importance_score=6.2)
    assert detector.should_track_as_incident(high_msg)

    low_msg = Message(2, "2", "c", "text", "text", now, importance_score=3.5)
    assert not detector.should_track_as_incident(low_msg)

    breaking_msg = Message(3, "3", "c", "text", "text", now, importance_score=8.7)
    assert detector.should_track_as_incident(breaking_msg)
