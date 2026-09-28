"""
Integration tests for storage layer and SQLAlchemy repositories using in-memory database.
"""

from datetime import datetime, timezone
import pytest
from app.domain.incidents import Incident, IncidentStatus, TimelineEntry
from app.domain.messages import Message
from app.domain.entities import NamedEntity, EntityType
from app.domain.claims import Claim
from app.storage.repositories.messages import SQLAlchemyMessageRepository
from app.storage.repositories.incidents import SQLAlchemyIncidentRepository
from app.storage.repositories.sources import SQLAlchemySourceRepository


@pytest.mark.asyncio
async def test_message_repository_crud(async_db_session):
    repo = SQLAlchemyMessageRepository(async_db_session)
    now = datetime.now(timezone.utc)

    msg = Message(
        id=None,
        external_id="ext-999",
        source_channel="tech_wire",
        text="Breakthrough in silicon photonics announced.",
        cleaned_text="Breakthrough in silicon photonics announced.",
        published_at=now,
        category="technology",
        importance_score=7.2,
    )

    saved = await repo.create(msg)
    assert saved.id is not None
    assert saved.external_id == "ext-999"

    fetched = await repo.get(saved.id)
    assert fetched is not None
    assert fetched.text == msg.text

    fetched.headline = "Silicon Photonics Leap"
    updated = await repo.update(fetched)
    assert updated.headline == "Silicon Photonics Leap"


@pytest.mark.asyncio
async def test_incident_repository_crud(async_db_session):
    repo = SQLAlchemyIncidentRepository(async_db_session)
    now = datetime.now(timezone.utc)

    incident = Incident(
        id=None,
        title="Silicon Photonics Revolution",
        category="technology",
        status=IncidentStatus.NEW,
        importance_score=7.5,
        summary="A major advance in optical computing.",
        sources=["tech_wire"],
        entities=[NamedEntity("TSMC", EntityType.ORGANIZATION, "tsmc")],
    )

    created = await repo.create(incident)
    assert created.id is not None

    entry = TimelineEntry(
        id=None,
        incident_id=created.id,
        timestamp=now,
        content="First commercial shipment",
        source_channel="tech_wire",
    )
    saved_entry = await repo.add_timeline_entry(entry)
    assert saved_entry.id is not None

    claim = Claim(
        id=None,
        incident_id=created.id,
        message_id=None,
        statement="Transistors operating at 10x efficiency.",
        source_name="tech_wire",
    )
    saved_claim = await repo.add_claim(claim)
    assert saved_claim.id is not None

    fetched = await repo.get(created.id)
    assert fetched is not None
    assert len(fetched.timeline) == 1
    assert len(fetched.claims) == 1
    assert len(fetched.entities) == 1


@pytest.mark.asyncio
async def test_source_repository_crud(async_db_session):
    repo = SQLAlchemySourceRepository(async_db_session)

    added = await repo.add_source("techcrunch", "TechCrunch News")
    assert added

    sources = await repo.list_active()
    assert "techcrunch" in sources

    removed = await repo.remove_source("techcrunch")
    assert removed

    sources_after = await repo.list_active()
    assert "techcrunch" not in sources_after
