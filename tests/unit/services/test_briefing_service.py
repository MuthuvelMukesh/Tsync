"""
Unit tests for briefing service.
"""

from app.domain.incidents import Incident, IncidentStatus, IncidentSeverity
from app.services.briefing_service import BriefingService


def test_generate_digest():
    service = BriefingService()

    inc1 = Incident(
        id=1,
        title="OpenAI launches GPT-5",
        category="technology",
        status=IncidentStatus.DEVELOPING,
        severity=IncidentSeverity.CRITICAL,
        importance_score=9.0,
        summary="Frontier AI model GPT-5 released.",
        sources=["source1", "source2"],
    )
    inc2 = Incident(
        id=2,
        title="Rate cuts signaled by Federal Reserve",
        category="finance",
        status=IncidentStatus.MONITORING,
        severity=IncidentSeverity.HIGH,
        importance_score=7.5,
        summary="Inflation cooled down to 2.4%.",
        sources=["source3"],
    )

    digest = service.generate_digest([inc1, inc2], period="hourly")

    assert digest.total_incidents == 2
    assert digest.breaking_count == 1
    assert "technology" in digest.category_distribution
    assert "finance" in digest.category_distribution
    assert digest.intensity in ["LOW", "MEDIUM", "HIGH"]
