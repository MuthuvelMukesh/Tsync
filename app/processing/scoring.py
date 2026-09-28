"""
Importance scoring engine.
Computes a heuristic 0–10 score using length, category weight, urgency, data specificity, and impact indicators.
"""

import re
from typing import Dict

CATEGORY_WEIGHTS: Dict[str, float] = {
    "technology": 1.5,
    "finance": 1.5,
    "geopolitics": 2.0,
    "regulation": 1.8,
    "science": 1.5,
    "jobs": 1.2,
    "other": 0.5,
}

URGENCY_KEYWORDS = [
    "breaking", "urgent", "just in", "alert", "confirmed", "confirms", "confirm",
    "official", "emergency", "unprecedented", "historic",
    "first time", "massive", "critical", "major", "threat",
]

IMPACT_PHRASES = [
    "for the first time", "all-time high", "all-time low",
    "record-breaking", "never before", "game changer",
    "paradigm shift", "disruption", "revolution",
    "billion", "trillion", "million users",
    "shut down", "acquired", "merged", "partnered",
    "launched", "announced", "revealed", "leaked",
    "discovery", "breakthrough", "unveiled",
]


def score_message(text: str, category: str = "other", source_channel: str = "") -> float:
    """Calculate importance score between 0.0 and 10.0."""
    score = 0.0
    text_lower = text.lower()

    # 1. Content Quality & Structure (0 - 2.0)
    words = text.split()
    word_count = len(words)
    if word_count >= 40:
        score += 1.5
    elif word_count >= 20:
        score += 1.0
    elif word_count >= 10:
        score += 0.5

    sentence_count = len(re.split(r"[.!?]+", text))
    if sentence_count >= 2:
        score += 0.5

    # 2. Category Relevance (0 - 2.0)
    score += CATEGORY_WEIGHTS.get(category, 0.5)

    # 3. Urgency Indicators (0 - 2.5)
    urgency_hits = sum(1 for kw in URGENCY_KEYWORDS if kw in text_lower)
    score += min(2.0, urgency_hits * 0.7)
    if "breaking" in text_lower[:25]:
        score += 0.8  # Direct breaking alert bonus

    # 4. Specificity & Data Density (0 - 2.0)
    numbers = re.findall(r"\b\d[\d,.]*[%$€£]?\b", text)
    if len(numbers) >= 3:
        score += 1.5
    elif len(numbers) >= 1:
        score += 0.8

    # Named entity pattern (capitalized word sequences)
    named_entities = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", text)
    if len(named_entities) >= 1:
        score += 0.5

    # 5. Novelty & Impact (0 - 2.0)
    impact_hits = sum(1 for p in IMPACT_PHRASES if p in text_lower)
    score += min(2.0, impact_hits * 0.7)

    return round(min(10.0, max(0.0, score)), 2)

