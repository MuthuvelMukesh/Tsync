"""
Unit tests for incident relationship mapper.
"""

from app.domain.entities import NamedEntity, EntityType
from app.domain.incidents import Incident
from app.incidents.relationships import IncidentRelationshipMapper


def test_find_related_by_entity():
    ent = NamedEntity("OpenAI", EntityType.ORGANIZATION, "openai")
    inc1 = Incident(1, "GPT-5 Launch", "tech", entities=[ent])
    inc2 = Incident(2, "OpenAI Funding Round", "finance", entities=[ent])

    mapper = IncidentRelationshipMapper()
    related = mapper.find_related(inc1, [inc1, inc2])

    assert len(related) == 1
    assert related[0][0].id == 2
    assert "Shares key entities" in related[0][1]
