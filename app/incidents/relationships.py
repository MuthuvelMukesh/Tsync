"""
Incident relationship mapper detecting conceptual links between active incidents.
"""

from typing import List, Tuple
from app.domain.incidents import Incident


class IncidentRelationshipMapper:
    """Discovers relationships between distinct incidents based on shared entities and themes."""

    @staticmethod
    def find_related(
        incident: Incident, other_incidents: List[Incident]
    ) -> List[Tuple[Incident, str]]:
        """Identify related incidents and relation description."""
        related = []
        incident_entities = {e.normalized_name for e in incident.entities}

        for other in other_incidents:
            if other.id == incident.id:
                continue

            other_entities = {e.normalized_name for e in other.entities}
            common_entities = incident_entities.intersection(other_entities)

            if common_entities:
                names = ", ".join(list(common_entities)[:3])
                related.append((other, f"Shares key entities: {names}"))
            elif other.category == incident.category and other.is_breaking:
                related.append((other, f"Concurrent high-impact in {incident.category}"))

        return related
