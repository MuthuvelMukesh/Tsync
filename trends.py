"""
trends.py — Trend detection and category analysis.

Identifies recurring themes, trending topics, and
category distribution from the selected messages.
"""

import re
from collections import Counter
from typing import Optional


# Common English stop words to exclude from trend analysis
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall",
    "can", "this", "that", "these", "those", "it", "its", "they",
    "them", "their", "we", "our", "you", "your", "he", "she", "him",
    "her", "his", "not", "no", "nor", "so", "if", "then", "than",
    "too", "very", "just", "about", "up", "out", "all", "also",
    "more", "most", "other", "some", "such", "into", "over",
    "after", "before", "between", "through", "during", "each",
    "new", "said", "via", "per", "via", "according", "which",
    "what", "when", "where", "how", "who", "whom", "why",
    "here", "there", "now", "only", "own", "same", "both",
    "any", "many", "much", "well", "still", "back", "even",
}


def extract_topics(messages: list[dict], top_n: int = 8) -> list[dict]:
    """
    Extract trending topics from messages using n-gram analysis.

    Returns list of {topic, count, relevance_score} dicts.
    """
    # Collect all text
    all_text = " ".join(m.get("text", "") for m in messages)

    # Clean text
    all_text = re.sub(r"https?://\S+", "", all_text)
    all_text = re.sub(r"[^\w\s]", " ", all_text)
    all_text = all_text.lower()

    words = all_text.split()
    words = [w for w in words if w not in STOP_WORDS and len(w) > 2]

    # Unigrams
    unigram_counts = Counter(words)

    # Bigrams (more meaningful topics)
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
    bigram_counts = Counter(bigrams)

    # Merge: prefer bigrams, supplement with unigrams
    topics = []

    for bigram, count in bigram_counts.most_common(top_n):
        if count >= 2:
            topics.append({
                "topic": bigram.title(),
                "count": count,
                "relevance_score": round(count / len(messages) * 10, 2),
            })

    # Fill remaining slots with unigrams
    remaining = top_n - len(topics)
    used_words = set()
    for t in topics:
        used_words.update(t["topic"].lower().split())

    for word, count in unigram_counts.most_common(remaining * 2):
        if len(topics) >= top_n:
            break
        if word not in used_words and count >= 2:
            topics.append({
                "topic": word.title(),
                "count": count,
                "relevance_score": round(count / len(messages) * 10, 2),
            })
            used_words.add(word)

    return topics[:top_n]


def category_breakdown(messages: list[dict]) -> dict[str, int]:
    """
    Get category distribution from messages.

    Returns dict of {category: count}.
    """
    categories = [m.get("category", "unknown") for m in messages]
    return dict(Counter(categories).most_common())


def detect_patterns(messages: list[dict]) -> list[str]:
    """
    Detect high-level patterns in the message set.

    Returns list of pattern description strings.
    """
    patterns = []

    cats = category_breakdown(messages)
    total = len(messages)

    if not total:
        return patterns

    # Dominant category detection
    for cat, count in cats.items():
        ratio = count / total
        if ratio >= 0.5:
            patterns.append(
                f"Dominant focus on {cat.title()} "
                f"({count}/{total} items, {ratio:.0%})"
            )
        elif ratio >= 0.3:
            patterns.append(
                f"Strong {cat.title()} presence "
                f"({count}/{total} items)"
            )

    # Score distribution
    scores = [m.get("importance_score", 0) for m in messages]
    if scores:
        avg = sum(scores) / len(scores)
        high_count = sum(1 for s in scores if s >= 7)
        if high_count >= 3:
            patterns.append(
                f"{high_count} high-impact items detected (score ≥ 7)"
            )
        if avg >= 6:
            patterns.append(
                f"Above-average news significance (mean score: {avg:.1f})"
            )

    # Multi-source detection
    channels = set(m.get("source_channel", "") for m in messages)
    if len(channels) >= 3:
        patterns.append(
            f"Cross-source corroboration from {len(channels)} channels"
        )

    return patterns
