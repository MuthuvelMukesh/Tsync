"""
Confidence scoring calculator for incidents and intelligence claims.
"""

from typing import List


class ConfidenceCalculator:
    """Calculates factual confidence based on multi-source corroboration and dispute signals."""

    @staticmethod
    def calculate_incident_confidence(
        sources: List[str],
        claims_count: int,
        contradictions_count: int,
        has_official_source: bool = False,
    ) -> float:
        """
        Derive a confidence score between 0.1 and 1.0.

        Factors:
        - Source diversity: more independent channels = higher confidence
        - Official sources: boosts confidence
        - Contradictions: lowers confidence
        """
        score = 0.5  # Base baseline

        # Source diversity
        unique_sources = len(set(sources))
        if unique_sources >= 4:
            score += 0.3
        elif unique_sources >= 2:
            score += 0.15

        # Official confirmation
        if has_official_source:
            score += 0.15

        # Claims volume
        if claims_count >= 3:
            score += 0.05

        # Contradictions penalty
        if contradictions_count > 0:
            score -= min(0.4, contradictions_count * 0.2)

        return round(min(1.0, max(0.1, score)), 2)
