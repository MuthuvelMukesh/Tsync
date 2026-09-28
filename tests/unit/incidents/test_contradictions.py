"""
Unit tests for contradiction detector.
"""

from app.domain.claims import Claim
from app.incidents.contradictions import ContradictionDetector


def test_detect_contradiction():
    detector = ContradictionDetector()

    c1 = Claim(
        id=1,
        incident_id=1,
        message_id=1,
        statement="Officials confirmed the pipeline was permanently closed.",
        source_name="source_a",
    )
    c2 = Claim(
        id=2,
        incident_id=1,
        message_id=2,
        statement="Ministry denies rumors of closure and rejects the reports as false.",
        source_name="source_b",
    )

    conflict = detector.detect_contradiction(c1, c2)
    assert conflict is not None
    assert conflict.severity == "high"


def test_no_contradiction_same_source():
    detector = ContradictionDetector()
    c1 = Claim(1, 1, 1, "Denies rumors", "source_a")
    c2 = Claim(2, 1, 2, "Confirms update", "source_a")
    assert detector.detect_contradiction(c1, c2) is None
