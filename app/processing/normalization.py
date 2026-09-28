"""
Text normalization, cleaning, and similarity computation.
"""

import hashlib
import re
import unicodedata
from typing import Set


def strip_urls(text: str) -> str:
    """Remove web links from text."""
    return re.sub(r"https?://\S+|www\.\S+", "", text).strip()


def clean_text(text: str) -> str:
    """Normalize unicode, whitespace, and strip decorative formatting."""
    if not text:
        return ""
    # NFKC normalizes unicode characters
    normalized = unicodedata.normalize("NFKC", text)
    # Remove control characters
    normalized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", normalized)
    # Collapse excess whitespace
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def generate_content_hash(text: str) -> str:
    """Compute sha256 hash of normalized text for deduplication."""
    clean = re.sub(r"\W+", "", text.lower())
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()


def tokenize_for_similarity(text: str) -> Set[str]:
    """Convert text into meaningful lowercased token set."""
    words = re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower())
    return set(words)


def compute_jaccard_similarity(text1: str, text2: str) -> float:
    """Compute token Jaccard similarity index (0.0 to 1.0)."""
    tokens1 = tokenize_for_similarity(text1)
    tokens2 = tokenize_for_similarity(text2)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union) if union else 0.0
