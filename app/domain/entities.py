"""
Domain model for named entities.
Independent of databases, frameworks, and third-party APIs.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EntityType(str, Enum):
    ORGANIZATION = "organization"
    PERSON = "person"
    LOCATION = "location"
    PRODUCT = "product"
    REGULATION = "regulation"
    FINANCIAL_INSTRUMENT = "financial_instrument"
    CONCEPT = "concept"
    OTHER = "other"


@dataclass(frozen=True)
class NamedEntity:
    """Represents a recognized entity within an intelligence context."""
    name: str
    entity_type: EntityType = EntityType.OTHER
    normalized_name: str = ""
    relevance_score: float = 1.0

    def __post_init__(self):
        if not self.normalized_name:
            object.__setattr__(self, "normalized_name", self.name.strip().lower())
