"""
rules.py — Rule-based categorization and filtering engine.

First stage of the hybrid pipeline. Uses keyword matching
and pattern detection to categorize messages WITHOUT AI calls.
Falls back to 'unknown' when confidence is low.
"""

import re
from typing import Optional

# ─── Category keyword maps ───────────────────────────────────────────────
# Each category has primary keywords (high confidence) and
# secondary keywords (medium confidence, need multiple matches).

CATEGORY_RULES: dict[str, dict] = {
    "technology": {
        "primary": [
            "AI", "artificial intelligence", "machine learning", "GPT",
            "LLM", "neural network", "deep learning", "blockchain",
            "cryptocurrency", "bitcoin", "ethereum", "software",
            "open source", "github", "API", "cloud computing",
            "cybersecurity", "data breach", "hack", "vulnerability",
            "5G", "quantum", "robotics", "semiconductor", "chip",
            "startup", "tech company", "silicon valley", "NVIDIA",
            "Google", "Microsoft", "Apple", "Meta", "OpenAI",
            "Amazon Web Services", "AWS", "Azure", "GPU",
        ],
        "secondary": [
            "app", "update", "release", "platform", "digital",
            "server", "database", "code", "developer", "launch",
            "model", "training", "compute", "algorithm",
        ],
    },
    "finance": {
        "primary": [
            "stock market", "S&P 500", "NASDAQ", "Dow Jones",
            "interest rate", "Federal Reserve", "inflation",
            "GDP", "recession", "IPO", "earnings", "revenue",
            "investment", "hedge fund", "venture capital",
            "bond", "treasury", "forex", "commodity",
            "banking", "fintech", "central bank", "monetary policy",
            "fiscal", "bull market", "bear market", "crypto market",
        ],
        "secondary": [
            "market", "price", "fund", "trading", "financial",
            "economy", "profit", "loss", "valuation", "growth",
            "shares", "equity", "capital", "budget",
        ],
    },
    "geopolitics": {
        "primary": [
            "sanctions", "NATO", "United Nations", "UN",
            "diplomacy", "treaty", "war", "conflict",
            "military", "nuclear", "missile", "invasion",
            "coup", "election", "regime", "alliance",
            "territory", "border", "geopolitical",
            "foreign policy", "embassy", "summit",
        ],
        "secondary": [
            "government", "president", "minister", "country",
            "nation", "political", "defense", "security",
            "intelligence", "cooperation", "dispute",
        ],
    },
    "jobs": {
        "primary": [
            "hiring", "layoff", "layoffs", "job opening",
            "recruitment", "remote work", "salary", "resume",
            "interview", "career", "unemployment",
            "workforce", "talent", "job market",
            "mass layoff", "downsizing", "restructuring",
        ],
        "secondary": [
            "employee", "position", "role", "team",
            "company", "work", "office", "job",
        ],
    },
    "science": {
        "primary": [
            "research", "study", "discovery", "scientific",
            "NASA", "SpaceX", "space", "climate change",
            "genome", "CRISPR", "vaccine", "clinical trial",
            "physics", "biology", "chemistry", "astronomy",
            "planet", "telescope", "fossil", "species",
        ],
        "secondary": [
            "experiment", "lab", "university", "professor",
            "journal", "published", "findings", "evidence",
        ],
    },
    "regulation": {
        "primary": [
            "regulation", "legislation", "bill", "law",
            "compliance", "SEC", "FTC", "EU regulation",
            "GDPR", "antitrust", "monopoly", "ban",
            "policy", "executive order", "legal",
        ],
        "secondary": [
            "rule", "enforce", "court", "ruling", "judge",
            "penalty", "fine", "approval",
        ],
    },
}

# ─── Spam / noise patterns ───────────────────────────────────────────────

SPAM_PATTERNS: list[str] = [
    r"(?i)join\s+(our|my)\s+(channel|group|telegram)",
    r"(?i)(subscribe|follow)\s+(now|us|here)",
    r"(?i)click\s+(here|the\s+link|below)",
    r"(?i)(buy|sell|discount|promo|offer|deal)\s+now",
    r"(?i)limited\s+time\s+offer",
    r"(?i)(earn|make)\s+\$?\d+.*?(daily|weekly|monthly)",
    r"(?i)🔥{2,}",
    r"(?i)(dm|message)\s+me\s+(for|to)",
    r"(?i)free\s+(money|crypto|bitcoin|giveaway)",
    r"(?i)100%\s+(guaranteed|profit|return)",
]

COMPILED_SPAM = [re.compile(p) for p in SPAM_PATTERNS]


def is_spam(text: str) -> bool:
    """Check if a message matches spam patterns."""
    for pattern in COMPILED_SPAM:
        if pattern.search(text):
            return True
    return False


def is_too_short(text: str, min_length: int = 30) -> bool:
    """Check if message is too short to be meaningful."""
    cleaned = re.sub(r"https?://\S+", "", text).strip()
    return len(cleaned) < min_length


def categorize_by_rules(text: str) -> tuple[str, float]:
    """
    Attempt rule-based categorization.

    Returns:
        (category, confidence) where confidence is 0.0–1.0.
        Returns ('unknown', 0.0) if no confident match.
    """
    text_upper = text.upper()
    text_lower = text.lower()

    scores: dict[str, float] = {}

    for category, keywords in CATEGORY_RULES.items():
        score = 0.0

        # Primary keywords → high weight
        for kw in keywords["primary"]:
            if kw.lower() in text_lower or kw.upper() in text_upper:
                score += 2.0

        # Secondary keywords → lower weight
        for kw in keywords["secondary"]:
            if kw.lower() in text_lower:
                score += 0.5

        if score > 0:
            scores[category] = score

    if not scores:
        return ("unknown", 0.0)

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    # Confidence thresholds
    if best_score >= 4.0:
        confidence = min(1.0, best_score / 8.0)
        return (best_category, confidence)
    elif best_score >= 2.0:
        confidence = best_score / 8.0
        return (best_category, confidence)
    else:
        return ("unknown", 0.0)


def prefilter_message(text: str) -> dict:
    """
    First-pass filter for a message.

    Returns a dict with filtering results:
    - skip: bool (should this message be skipped entirely?)
    - reason: str (why it was skipped)
    - category: str (if categorized by rules)
    - confidence: float (rule confidence)
    - needs_ai: bool (should AI process this?)
    """
    # Check for spam
    if is_spam(text):
        return {
            "skip": True,
            "reason": "spam",
            "category": "spam",
            "confidence": 1.0,
            "needs_ai": False,
        }

    # Check for too-short messages
    if is_too_short(text):
        return {
            "skip": True,
            "reason": "too_short",
            "category": "noise",
            "confidence": 1.0,
            "needs_ai": False,
        }

    # Attempt rule-based categorization
    category, confidence = categorize_by_rules(text)

    if confidence >= 0.5:
        return {
            "skip": False,
            "reason": None,
            "category": category,
            "confidence": confidence,
            "needs_ai": False,  # Rules handled it
        }
    else:
        return {
            "skip": False,
            "reason": None,
            "category": category if category != "unknown" else None,
            "confidence": confidence,
            "needs_ai": True,  # Fall back to AI
        }
