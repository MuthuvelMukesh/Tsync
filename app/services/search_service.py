"""
Search service providing domain-oriented querying for incidents and entities.
Decouples bot adapters and report generators from persistence schemas.
"""

from datetime import datetime
from typing import List, Optional

from app.domain.entities import NamedEntity
from app.domain.incidents import Incident, IncidentStatus
from app.storage.repositories.entities import EntityRepository
from app.storage.repositories.incidents import IncidentRepository


class SearchService:
    """Provides high-level search across incidents and named entities."""

    def __init__(
        self,
        incident_repo: IncidentRepository,
        entity_repo: Optional[EntityRepository] = None,
    ):
        self.incident_repo = incident_repo
        self.entity_repo = entity_repo

    async def search_incidents(self, query: str, limit: int = 20) -> List[Incident]:
        """Search incidents matching query text across title, summary, and impact."""
        return await self.incident_repo.search(query=query, limit=limit)

    async def search_entities(self, entity_name: str) -> List[NamedEntity]:
        """Search named entities."""
        if not self.entity_repo:
            return []
        return await self.entity_repo.search(name_query=entity_name)

    async def search_by_category(self, category: str, limit: int = 20) -> List[Incident]:
        """Find incidents belonging to a specific category."""
        return await self.incident_repo.search(query="", category=category, limit=limit)

    async def search_by_date(
        self, start: datetime, end: datetime, limit: int = 50
    ) -> List[Incident]:
        """Find incidents updated within a given time range."""
        active = await self.incident_repo.list_active()
        return [
            inc for inc in active
            if inc.updated_at and start <= inc.updated_at <= end
        ][:limit]

    async def search_active_incidents(self) -> List[Incident]:
        """Return currently active incidents (NEW, DEVELOPING, MONITORING)."""
        return await self.incident_repo.list_active()
