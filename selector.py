"""
selector.py — Dynamic message selection engine.

Selects high-value messages using adaptive thresholds
instead of fixed Top-N limits. Ensures quality over quantity.
"""

import json
import statistics
from typing import Optional


def load_config() -> dict:
    """Load configuration."""
    with open("config.json", "r") as f:
        return json.load(f)


def dynamic_select(
    messages: list[dict],
    min_items: int = 5,
    max_items: int = 15,
    threshold: Optional[float] = None,
) -> list[dict]:
    """
    Dynamically select high-value messages.

    Strategy:
    1. Calculate score distribution statistics
    2. Set adaptive threshold at 75th percentile (or config value)
    3. Select items above threshold
    4. Enforce min/max bounds
    5. Sort by importance descending

    Args:
        messages: List of scored message dicts
        min_items: Minimum items to select
        max_items: Maximum items to select
        threshold: Override threshold (uses adaptive if None)

    Returns:
        Selected messages sorted by importance
    """
    if not messages:
        return []

    config = load_config()
    min_items = config.get("min_items", min_items)
    max_items = config.get("max_items", max_items)

    # Sort by importance score descending
    sorted_msgs = sorted(
        messages,
        key=lambda m: m.get("importance_score", 0),
        reverse=True,
    )

    scores = [m.get("importance_score", 0) for m in sorted_msgs]

    if not scores:
        return []

    # ─── Calculate adaptive threshold ────────────────────────────────
    if threshold is None:
        config_threshold = config.get("importance_threshold", 7)

        if len(scores) >= 4:
            # Use 75th percentile as base
            p75 = _percentile(scores, 75)
            mean_score = statistics.mean(scores)
            std_score = statistics.stdev(scores) if len(scores) > 1 else 0

            # Adaptive: use the higher of p75 or (mean + 0.5*std)
            adaptive = max(p75, mean_score + 0.5 * std_score)

            # But don't exceed config threshold too much
            threshold = min(adaptive, config_threshold)

            # Floor: never go below 3.0 (absolute minimum quality)
            threshold = max(3.0, threshold)
        else:
            threshold = config_threshold

    print(f"[SELECTOR] Adaptive threshold: {threshold:.2f}")
    print(f"[SELECTOR] Score range: {min(scores):.2f} – {max(scores):.2f}")
    print(f"[SELECTOR] Mean: {statistics.mean(scores):.2f}")

    # ─── Select messages above threshold ─────────────────────────────
    selected = [m for m in sorted_msgs if m.get("importance_score", 0) >= threshold]

    # ─── Enforce bounds ──────────────────────────────────────────────
    if len(selected) < min_items:
        # Take top min_items regardless of threshold
        selected = sorted_msgs[:min_items]
        print(f"[SELECTOR] Below minimum, expanded to {min_items} items")
    elif len(selected) > max_items:
        # Trim to max
        selected = selected[:max_items]
        print(f"[SELECTOR] Above maximum, trimmed to {max_items} items")

    print(f"[SELECTOR] Selected {len(selected)} / {len(messages)} messages")
    return selected


def calculate_intensity(
    total_messages: int,
    selected_count: int,
    avg_score: float,
) -> str:
    """
    Calculate news intensity level.

    Returns: 'LOW', 'MEDIUM', or 'HIGH'
    """
    # Weighted intensity score
    intensity_score = 0

    # Volume factor
    if total_messages >= 80:
        intensity_score += 3
    elif total_messages >= 40:
        intensity_score += 2
    elif total_messages >= 15:
        intensity_score += 1

    # Quality factor
    if avg_score >= 7.0:
        intensity_score += 3
    elif avg_score >= 5.0:
        intensity_score += 2
    elif avg_score >= 3.0:
        intensity_score += 1

    # Selection ratio
    if selected_count >= 12:
        intensity_score += 2
    elif selected_count >= 8:
        intensity_score += 1

    if intensity_score >= 6:
        return "HIGH"
    elif intensity_score >= 3:
        return "MEDIUM"
    else:
        return "LOW"


def _percentile(data: list[float], pct: float) -> float:
    """Calculate percentile of sorted data."""
    sorted_data = sorted(data, reverse=True)
    k = (len(sorted_data) - 1) * (1 - pct / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    d = k - f
    return sorted_data[f] * (1 - d) + sorted_data[c] * d
