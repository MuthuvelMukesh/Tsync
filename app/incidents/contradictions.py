"""
Contradiction detector identifying conflicting claims and dispute signals.
"""

from datetime import datetime, timezone
import re
from typing import List, Optional
from app.domain.claims import Claim, Contradiction

OPPOSING_PATTERNS = [
    (r"\b(denies|denied|rejects|rejected|false)\b", r"\b(confirmed|confirms|verified|true)\b"),
    (r"\b(killed|dead|fatalities)\b", r"\b(survived|unharmed|no casualties)\b"),
    (r"\b(rises|increased|gain|surged)\b", r"\b(fell|decreased|loss|dropped|plunged)\b"),
    (r"\b(banned|prohibited|blocked)\b", r"\b(approved|permitted|allowed|greenlit)\b"),
]


class ContradictionDetector:
    """Detects factual disputes between extracted claims."""

    @staticmethod
    def detect_contradiction(
        claim_a: Claim, claim_b: Claim
    ) -> Optional[Contradiction]:
        """Check if two claims contain opposing assertions."""
        if claim_a.source_name == claim_b.source_name:
            return None

        text_a = claim_a.statement.lower()
        text_b = claim_b.statement.lower()

        for pat_a, pat_b in OPPOSING_PATTERNS:
            match_a1 = re.search(pat_a, text_a)
            match_b2 = re.search(pat_b, text_b)
            if match_a1 and match_b2:
                return Contradiction(
                    claim_a=claim_a,
                    claim_b=claim_b,
                    explanation=f"Conflict detected between '{match_a1.group()}' and '{match_b2.group()}'",
                    severity="high",
                    detected_at=datetime.now(timezone.utc),
                )

            match_a2 = re.search(pat_b, text_a)
            match_b1 = re.search(pat_a, text_b)
            if match_a2 and match_b1:
                return Contradiction(
                    claim_a=claim_a,
                    claim_b=claim_b,
                    explanation=f"Conflict detected between '{match_a2.group()}' and '{match_b1.group()}'",
                    severity="high",
                    detected_at=datetime.now(timezone.utc),
                )

        return None

    def find_all_contradictions(self, claims: List[Claim]) -> List[Contradiction]:
        """Evaluate all claim pairs in an incident for discrepancies."""
        contradictions: List[Contradiction] = []
        n = len(claims)
        for i in range(n):
            for j in range(i + 1, n):
                conflict = self.detect_contradiction(claims[i], claims[j])
                if conflict:
                    contradictions.append(conflict)
        return contradictions
