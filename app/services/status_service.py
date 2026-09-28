"""
Status service providing operational health and statistics.
"""

from typing import Dict, Any
from app.storage.repositories.incidents import IncidentRepository
from app.storage.repositories.sources import SourceRepository


class StatusService:
    """Aggregates health, source counts, and active incidents for bot and monitoring."""

    def __init__(
        self,
        incident_repo: IncidentRepository,
        source_repo: SourceRepository,
    ):
        self.incident_repo = incident_repo
        self.source_repo = source_repo

    async def get_system_status(self) -> Dict[str, Any]:
        """Collect current system status metrics."""
        active_sources = await self.source_repo.list_active()
        active_incidents = await self.incident_repo.list_active()

        breaking_count = sum(1 for i in active_incidents if i.is_breaking)
        categories = set(i.category for i in active_incidents)

        return {
            "status": "healthy",
            "active_sources_count": len(active_sources),
            "sources": active_sources,
            "active_incidents_count": len(active_incidents),
            "breaking_incidents_count": breaking_count,
            "monitored_categories": list(categories),
        }
