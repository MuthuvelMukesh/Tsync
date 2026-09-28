"""
Filtering engine for rejecting spam, advertisements, and low-quality noise.
"""

import re
from typing import List

from app.domain.messages import RawMessage, MessageFilterResult

SPAM_PATTERNS: List[str] = [
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
    r"(?i)casino|betting|poker|slots|jackpot",
]

COMPILED_SPAM = [re.compile(p) for p in SPAM_PATTERNS]


def is_spam(text: str) -> bool:
    """Check if message matches recognized promotional or spam patterns."""
    return any(p.search(text) for p in COMPILED_SPAM)


def is_too_short(text: str, min_length: int = 30) -> bool:
    """Check if text (excluding URLs) falls below meaningful threshold."""
    cleaned = re.sub(r"https?://\S+", "", text).strip()
    return len(cleaned) < min_length


def filter_raw_message(raw: RawMessage, min_length: int = 30) -> MessageFilterResult:
    """Evaluate raw incoming message for noise and discard reasons."""
    text = raw.text or ""
    if is_spam(text):
        return MessageFilterResult(
            should_skip=True,
            reason="spam",
            rule_category="spam",
            rule_confidence=1.0,
            needs_ai_fallback=False,
        )

    if is_too_short(text, min_length=min_length):
        return MessageFilterResult(
            should_skip=True,
            reason="too_short",
            rule_category="noise",
            rule_confidence=1.0,
            needs_ai_fallback=False,
        )

    return MessageFilterResult(
        should_skip=False,
        reason=None,
        rule_category=None,
        rule_confidence=0.0,
        needs_ai_fallback=False,
    )
