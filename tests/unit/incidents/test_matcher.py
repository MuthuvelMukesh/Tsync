"""
Unit tests for incident matcher.
"""

from datetime import datetime, timezone
from app.domain.entities import NamedEntity, EntityType
from app.domain.incidents import Incident, IncidentStatus
from app.domain.messages import Message
from app.incidents.matcher import IncidentMatcher


def test_matcher_finds_best_candidate():
    matcher = IncidentMatcher(match_threshold=0.25)
    now = datetime.now(timezone.utc)

    incident = Incident(
        id=1,
        title="OpenAI Unveils GPT-5 Frontier Model",
        category="technology",
        status=IncidentStatus.DEVELOPING,
        summary="OpenAI has released the next generation reasoning model GPT-5.",
        entities=[NamedEntity(name="OpenAI", entity_type=EntityType.ORGANIZATION, normalized_name="openai")],
    )

    msg_related = Message(
        id=10,
        external_id="10",
        source_channel="tech_radar",
        text="OpenAI confirms enterprise partners getting GPT-5 API access starting next month.",
        cleaned_text="OpenAI confirms enterprise partners getting GPT-5 API access starting next month.",
        published_at=now,
        category="technology",
    )

    matched, score = matcher.find_best_match(msg_related, [incident])
    assert matched is not None
    assert matched.id == 1
    assert score > 0.25


def test_matcher_rejects_unrelated():
    matcher = IncidentMatcher(match_threshold=0.25)
    now = datetime.now(timezone.utc)

    incident = Incident(
        id=1,
        title="OpenAI Unveils GPT-5 Frontier Model",
        category="technology",
        status=IncidentStatus.DEVELOPING,
        summary="OpenAI has released the next generation reasoning model GPT-5.",
    )

    msg_unrelated = Message(
        id=20,
        external_id="20",
        source_channel="agri_wire",
        text="Wheat harvests in Argentina exceed previous drought expectations.",
        cleaned_text="Wheat harvests in Argentina exceed previous drought expectations.",
        published_at=now,
        category="finance",
    )

    matched, score = matcher.find_best_match(msg_unrelated, [incident])
    assert matched is None
    assert score == 0.0
