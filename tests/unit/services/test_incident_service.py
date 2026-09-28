"""
Unit tests for incident service.
"""

from datetime import datetime, timezone
import pytest
from app.domain.events import EventDispatcher, IncidentCreated
from app.domain.incidents import Incident, IncidentStatus
from app.domain.messages import Message
from app.services.incident_service import IncidentService


class MockIncidentRepository:
    def __init__(self):
        self.incidents = {}
        self.counter = 1
        self.timeline_entries = []
        self.claims = []

    async def get(self, incident_id: int):
        return self.incidents.get(incident_id)

    async def create(self, incident: Incident):
        incident.id = self.counter
        self.counter += 1
        self.incidents[incident.id] = incident
        return incident

    async def update(self, incident: Incident):
        self.incidents[incident.id] = incident
        return incident

    async def find_candidates(self, message: Message):
        return list(self.incidents.values())

    async def list_active(self):
        return list(self.incidents.values())

    async def add_timeline_entry(self, entry):
        entry.id = len(self.timeline_entries) + 1
        self.timeline_entries.append(entry)
        return entry

    async def add_claim(self, claim):
        claim.id = len(self.claims) + 1
        self.claims.append(claim)
        return claim


class MockMessageRepository:
    async def update(self, message: Message):
        return message


@pytest.mark.asyncio
async def test_incident_service_creates_incident():
    inc_repo = MockIncidentRepository()
    msg_repo = MockMessageRepository()
    dispatcher = EventDispatcher()

    created_events = []
    dispatcher.subscribe(IncidentCreated, lambda e: created_events.append(e))

    service = IncidentService(
        incident_repo=inc_repo,
        message_repo=msg_repo,
        event_dispatcher=dispatcher,
    )

    now = datetime.now(timezone.utc)
    msg = Message(
        id=10,
        external_id="ext-10",
        source_channel="tech_radar",
        text="BREAKING: Major breakthrough announced in solid-state battery energy storage.",
        cleaned_text="BREAKING: Major breakthrough announced in solid-state battery energy storage.",
        published_at=now,
        category="technology",
        importance_score=8.5,
        headline="Solid-State Battery Breakthrough",
    )

    result = await service.process_message(msg)

    assert result is not None
    assert result.created
    assert result.incident.id == 1
    assert result.incident.title == "Solid-State Battery Breakthrough"
    assert len(created_events) == 1
