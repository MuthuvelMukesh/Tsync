"""
End-to-End test for full incident lifecycle:
Raw Message Ingest → Filtering → Categorization → Scoring → Incident Creation (NEW)
→ Corroborating Source → Status Progression (DEVELOPING) → Timeline
→ Briefing Digest Generation → Resolution (RESOLVED)
"""

from datetime import datetime, timezone
import pytest

from app.domain.events import EventDispatcher, IncidentCreated, IncidentUpdated
from app.domain.incidents import IncidentStatus, IncidentSeverity
from app.domain.messages import Message
from app.processing.categorization import categorize_by_rules
from app.processing.normalization import clean_text
from app.processing.scoring import score_message
from app.services.briefing_service import BriefingService
from app.services.incident_service import IncidentService
from app.storage.repositories.incidents import SQLAlchemyIncidentRepository
from app.storage.repositories.messages import SQLAlchemyMessageRepository


@pytest.mark.asyncio
async def test_full_incident_lifecycle_e2e(async_db_session):
    incident_repo = SQLAlchemyIncidentRepository(async_db_session)
    message_repo = SQLAlchemyMessageRepository(async_db_session)
    dispatcher = EventDispatcher()
    briefing_service = BriefingService()

    events_log = []
    dispatcher.subscribe(IncidentCreated, lambda e: events_log.append("CREATED"))
    dispatcher.subscribe(IncidentUpdated, lambda e: events_log.append("UPDATED"))

    incident_service = IncidentService(
        incident_repo=incident_repo,
        message_repo=message_repo,
        event_dispatcher=dispatcher,
    )

    now = datetime.now(timezone.utc)

    # ─── PHASE 1: Message 1 Arrives (Initial Incident Creation) ───
    text_1 = "BREAKING: NASA confirms discovery of organic molecules on Mars Jezero Crater."
    cat_1, _ = categorize_by_rules(text_1)
    score_1 = score_message(text_1, category=cat_1, source_channel="science_wire")

    msg_1 = Message(
        id=None,
        external_id="nasa-001",
        source_channel="science_wire",
        text=text_1,
        cleaned_text=clean_text(text_1),
        published_at=now,
        category=cat_1,
        importance_score=score_1,
        headline="NASA Confirms Organic Molecules on Mars",
    )
    saved_msg_1 = await message_repo.create(msg_1)

    result_1 = await incident_service.process_message(saved_msg_1)
    assert result_1 is not None
    assert result_1.created
    assert result_1.incident.status == IncidentStatus.NEW
    assert result_1.incident.sources == ["science_wire"]
    assert "CREATED" in events_log

    incident_id = result_1.incident.id

    # ─── PHASE 2: Message 2 Arrives (Corroborating from 2nd Source) ───
    text_2 = "Perseverance rover scientists in Jezero Crater verify complex carbon structures on Mars."
    cat_2, _ = categorize_by_rules(text_2)
    score_2 = score_message(text_2, category=cat_2, source_channel="space_daily")

    msg_2 = Message(
        id=None,
        external_id="space-002",
        source_channel="space_daily",
        text=text_2,
        cleaned_text=clean_text(text_2),
        published_at=now,
        category=cat_2,
        importance_score=score_2,
        headline="Scientists Verify Complex Carbon on Mars",
    )
    saved_msg_2 = await message_repo.create(msg_2)

    result_2 = await incident_service.process_message(saved_msg_2)
    assert result_2 is not None
    assert not result_2.created  # Matched existing incident
    assert result_2.incident.id == incident_id

    # Verified multi-source progression to DEVELOPING
    assert result_2.incident.status == IncidentStatus.DEVELOPING
    assert set(result_2.incident.sources) == {"science_wire", "space_daily"}
    assert result_2.is_material_change
    assert "UPDATED" in events_log

    # ─── PHASE 3: Verify Persistence & Timeline ────────────────────
    persisted = await incident_repo.get(incident_id)
    assert persisted is not None
    assert len(persisted.timeline) == 2
    assert len(persisted.claims) == 2

    # ─── PHASE 4: Generate Briefing Digest ─────────────────────────
    digest = briefing_service.generate_digest([persisted], period="hourly")
    assert digest.total_incidents == 1
    assert "science" in digest.category_distribution

    # ─── PHASE 5: Lifecycle Transition to RESOLVED ─────────────────
    persisted.transition_to(IncidentStatus.MONITORING)
    await incident_repo.update(persisted)

    persisted.transition_to(IncidentStatus.RESOLVED)
    updated_resolved = await incident_repo.update(persisted)
    assert updated_resolved.status == IncidentStatus.RESOLVED
    assert updated_resolved.resolved_at is not None
