"""
Unit tests for status service.
"""

import pytest
from app.domain.incidents import Incident
from app.services.status_service import StatusService


class MockStatusIncRepo:
    async def list_active(self):
        return [
            Incident(1, "Breaking Incident", "tech", importance_score=9.0),
            Incident(2, "Normal Incident", "finance", importance_score=6.0),
        ]


class MockStatusSourceRepo:
    async def list_active(self):
        return ["techcrunch", "bloomberg"]


@pytest.mark.asyncio
async def test_status_service():
    service = StatusService(
        incident_repo=MockStatusIncRepo(),
        source_repo=MockStatusSourceRepo(),
    )
    status = await service.get_system_status()

    assert status["status"] == "healthy"
    assert status["active_sources_count"] == 2
    assert status["active_incidents_count"] == 2
    assert status["breaking_incidents_count"] == 1
