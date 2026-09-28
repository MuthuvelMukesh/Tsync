"""
Unit tests for domain entities.
"""

from app.domain.entities import NamedEntity, EntityType


def test_named_entity_normalization():
    ent = NamedEntity(name="  Microsoft Corp  ", entity_type=EntityType.ORGANIZATION)
    assert ent.normalized_name == "microsoft corp"
    assert ent.entity_type == EntityType.ORGANIZATION
    assert ent.relevance_score == 1.0


def test_named_entity_frozen():
    ent = NamedEntity(name="NVIDIA", entity_type=EntityType.ORGANIZATION)
    assert ent.name == "NVIDIA"
