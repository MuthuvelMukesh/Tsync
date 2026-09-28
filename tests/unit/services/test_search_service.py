"""
Unit tests for search service.
"""

import pytest
from app.domain.incidents import Incident, IncidentStatus
from app.services.search_service import SearchService


class MockSearchRepo:
    def __init__(self, incidents):
        self._incidents = incidents

    async def search(self, query: str, category=None, limit=20):
        res = self._incidents
        if query:
            res = [i for i in res if query.lower() in i.title.lower()]
        if category:
            res = [i for i in res if i.category == category]
        return res[:limit]

    async def list_active(self):
        return self._incidents


@pytest.mark.asyncio
async def test_search_incidents():
    inc1 = Incident(1, "Semiconductor subsidies announced", "technology")
    inc2 = Incident(2, "Federal interest rates update", "finance")
    repo = MockSearchRepo([inc1, inc2])

    service = SearchService(incident_repo=repo)

    res = await service.search_incidents("Semiconductor")
    assert len(res) == 1
    assert res[0].id == 1

    cat_res = await service.search_by_category("finance")
    assert len(cat_res) == 1
    assert cat_res[0].id == 2
