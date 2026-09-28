"""
Unit tests for domain claims and contradictions.
"""

from app.domain.claims import Claim, Contradiction


def test_claim_creation():
    claim = Claim(
        id=1,
        incident_id=10,
        message_id=5,
        statement="Company revenue grew 40%",
        source_name="reuters",
        confidence=0.9,
    )
    assert claim.statement == "Company revenue grew 40%"
    assert not claim.is_disputed


def test_contradiction_creation():
    c1 = Claim(id=1, incident_id=1, message_id=1, statement="Minister denies rumor", source_name="src1")
    c2 = Claim(id=2, incident_id=1, message_id=2, statement="Minister confirms deal", source_name="src2")
    contra = Contradiction(claim_a=c1, claim_b=c2, explanation="Denies vs Confirms", severity="high")
    assert contra.severity == "high"
