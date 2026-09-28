"""
Unit tests for domain events and event dispatcher.
"""

import pytest
from app.domain.events import (
    EventDispatcher,
    IncidentCreated,
    IncidentUpdated,
    DomainEvent,
)
from app.domain.incidents import Incident


@pytest.mark.asyncio
async def test_event_dispatcher_pubsub(sample_incident):
    dispatcher = EventDispatcher()
    received_events = []

    async def on_incident_created(event: IncidentCreated):
        received_events.append(event)

    dispatcher.subscribe(IncidentCreated, on_incident_created)

    event = IncidentCreated(incident=sample_incident)
    await dispatcher.publish(event)

    assert len(received_events) == 1
    assert received_events[0].incident.title == sample_incident.title


@pytest.mark.asyncio
async def test_event_dispatcher_base_class_subscription(sample_incident):
    dispatcher = EventDispatcher()
    all_events = []

    def on_any_domain_event(event: DomainEvent):
        all_events.append(event)

    dispatcher.subscribe(DomainEvent, on_any_domain_event)

    await dispatcher.publish(IncidentCreated(incident=sample_incident))
    await dispatcher.publish(IncidentUpdated(incident=sample_incident, is_material_change=True))

    assert len(all_events) == 2
