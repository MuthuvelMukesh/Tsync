"""
Processing pipeline modules: filtering, normalization, categorization, and scoring.
"""

from app.processing.filtering import filter_raw_message, is_spam, is_too_short
from app.processing.normalization import (
    clean_text,
    strip_urls,
    generate_content_hash,
    compute_jaccard_similarity,
)
from app.processing.categorization import categorize_by_rules, CATEGORY_RULES
from app.processing.scoring import score_message

__all__ = [
    "filter_raw_message",
    "is_spam",
    "is_too_short",
    "clean_text",
    "strip_urls",
    "generate_content_hash",
    "compute_jaccard_similarity",
    "categorize_by_rules",
    "CATEGORY_RULES",
    "score_message",
]
