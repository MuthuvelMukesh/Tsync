"""
scorer.py — Message importance scoring engine.

Scores messages on a 0–10 scale using multiple heuristic signals.
Designed to run WITHOUT AI calls for maximum efficiency.
"""

import re
from datetime import datetime


def score_message(text: str, category: str, source_channel: str) -> float:
    """
    Score a message's importance on a 0–10 scale.

    Scoring factors:
    1. Content length & density
    2. Category relevance
    3. Urgency signals
    4. Specificity (numbers, names, data)
    5. Novelty indicators
    """
    score = 0.0

    # ─── 1. Content Quality (0–2.0) ──────────────────────────────────
    word_count = len(text.split())
    if word_count >= 50:
        score += 1.5
    elif word_count >= 30:
        score += 1.0
    elif word_count >= 15:
        score += 0.5

    # Sentences → more structured content
    sentence_count = len(re.split(r"[.!?]+", text))
    if sentence_count >= 3:
        score += 0.5

    # ─── 2. Category Weight (0–2.0) ──────────────────────────────────
    category_weights = {
        "technology": 1.5,
        "finance": 1.5,
        "geopolitics": 2.0,
        "regulation": 1.8,
        "science": 1.5,
        "jobs": 1.2,
        "unknown": 0.5,
    }
    score += category_weights.get(category, 0.5)

    # ─── 3. Urgency Signals (0–2.0) ──────────────────────────────────
    urgency_keywords = [
        "breaking", "urgent", "just in", "alert",
        "confirmed", "official", "emergency",
        "unprecedented", "historic", "first time",
        "massive", "critical", "major",
    ]
    urgency_hits = sum(
        1 for kw in urgency_keywords if kw.lower() in text.lower()
    )
    score += min(2.0, urgency_hits * 0.5)

    # ─── 4. Specificity (0–2.0) ──────────────────────────────────────
    # Numbers and statistics → more concrete
    numbers = re.findall(r"\b\d[\d,.]*[%$€£]?\b", text)
    if len(numbers) >= 3:
        score += 1.5
    elif len(numbers) >= 1:
        score += 0.8

    # Named entities (capitalized multi-word phrases)
    named_entities = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", text)
    if len(named_entities) >= 2:
        score += 0.5

    # ─── 5. Novelty & Impact (0–2.0) ─────────────────────────────────
    impact_phrases = [
        "for the first time", "all-time high", "all-time low",
        "record-breaking", "never before", "game changer",
        "paradigm shift", "disruption", "revolution",
        "billion", "trillion", "million users",
        "shut down", "acquired", "merged", "partnered",
        "launched", "announced", "revealed", "leaked",
    ]
    impact_hits = sum(
        1 for phrase in impact_phrases if phrase.lower() in text.lower()
    )
    score += min(2.0, impact_hits * 0.7)

    # ─── Clamp to 0–10 ──────────────────────────────────────────────
    return round(min(10.0, max(0.0, score)), 2)


def batch_score(messages: list[dict]) -> list[dict]:
    """
    Score a batch of messages in-place.

    Each message dict must have 'text', 'category', 'source_channel'.
    Adds 'importance_score' to each.
    """
    for msg in messages:
        msg["importance_score"] = score_message(
            msg["text"],
            msg.get("category", "unknown"),
            msg.get("source_channel", ""),
        )
    return messages
