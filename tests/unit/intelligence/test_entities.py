"""
Unit tests for entity extractor.
"""

from app.intelligence.entities import EntityExtractor
from app.domain.entities import EntityType


def test_extract_known_entities():
    text = "OpenAI and Microsoft signed agreements regarding compute in Japan."
    entities = EntityExtractor.extract_entities(text)

    names = {e.normalized_name for e in entities}
    assert "openai" in names
    assert "microsoft" in names
    assert "japan" in names
