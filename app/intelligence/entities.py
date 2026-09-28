"""
Entity extraction and normalization utilities.
"""

import re
from typing import List, Set
from app.domain.entities import NamedEntity, EntityType

KNOWN_ORGS = {
    "openai", "google", "microsoft", "apple", "meta", "nvidia", "amazon",
    "tesla", "spacex", "nato", "un", "united nations", "federal reserve", "fed",
    "sec", "ftc", "tsmc", "fbi", "nasa", "deepmind", "anthropic", "blackrock",
}

KNOWN_LOCATIONS = {
    "us", "usa", "china", "eu", "europe", "uk", "taiwan", "russia", "ukraine",
    "japan", "india", "gujarat", "beijing", "washington", "mars",
}


class EntityExtractor:
    """Extracts named entities from text using heuristics and pattern matching."""

    @staticmethod
    def extract_entities(text: str) -> List[NamedEntity]:
        entities: List[NamedEntity] = []
        seen: Set[str] = set()

        text_lower = text.lower()

        # 1. Match known organizations
        for org in KNOWN_ORGS:
            pattern = rf"\b{re.escape(org)}\b"
            if re.search(pattern, text_lower):
                if org not in seen:
                    entities.append(
                        NamedEntity(
                            name=org.upper() if len(org) <= 4 else org.title(),
                            entity_type=EntityType.ORGANIZATION,
                            normalized_name=org,
                            relevance_score=1.5,
                        )
                    )
                    seen.add(org)

        # 2. Match known locations
        for loc in KNOWN_LOCATIONS:
            pattern = rf"\b{re.escape(loc)}\b"
            if re.search(pattern, text_lower):
                if loc not in seen:
                    entities.append(
                        NamedEntity(
                            name=loc.upper() if len(loc) <= 3 else loc.title(),
                            entity_type=EntityType.LOCATION,
                            normalized_name=loc,
                            relevance_score=1.2,
                        )
                    )
                    seen.add(loc)

        # 3. Capitalized multi-word entities (e.g. Jensen Huang, South China Sea, Jezero Crater)
        capitalized = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", text)
        for cand in capitalized:
            norm = cand.strip().lower()
            if norm not in seen and len(norm) > 4:
                entities.append(
                    NamedEntity(
                        name=cand.strip(),
                        entity_type=EntityType.OTHER,
                        normalized_name=norm,
                        relevance_score=1.0,
                    )
                )
                seen.add(norm)

        return entities
