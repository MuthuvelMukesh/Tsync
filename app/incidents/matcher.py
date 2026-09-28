"""
Incident matcher comparing incoming messages against candidate active incidents.
"""

from typing import List, Optional, Tuple

from app.domain.incidents import Incident
from app.domain.messages import Message
from app.processing.normalization import compute_jaccard_similarity


class IncidentMatcher:
    """Matches a message with candidate incidents using category, text similarity, and entities."""

    def __init__(self, match_threshold: float = 0.28):
        self.match_threshold = match_threshold

    def find_best_match(
        self, message: Message, candidates: List[Incident]
    ) -> Tuple[Optional[Incident], float]:
        """
        Evaluate candidates and return (best_incident, confidence_score).
        Returns (None, 0.0) if no candidate exceeds match_threshold.
        """
        if not candidates:
            return None, 0.0

        best_incident: Optional[Incident] = None
        best_score: float = 0.0

        msg_text = message.cleaned_text or message.text
        msg_words = set(msg_text.lower().split())

        for cand in candidates:
            score = 0.0

            # 1. Category alignment
            if cand.category == message.category:
                score += 0.15

            # 2. Text similarity with title and summary
            title_sim = compute_jaccard_similarity(msg_text, cand.title)
            summary_sim = compute_jaccard_similarity(msg_text, cand.summary)
            score += max(title_sim * 0.5, summary_sim * 0.4)

            # 3. Entity overlap
            for ent in cand.entities:
                if ent.normalized_name in msg_text.lower():
                    score += 0.25
                    break

            # 4. Keyword token overlap
            cand_tokens = set((cand.title + " " + cand.summary).lower().split())
            common_tokens = msg_words.intersection(cand_tokens)
            if len(common_tokens) >= 4:
                score += 0.15

            if score > best_score:
                best_score = score
                best_incident = cand

        if best_score >= self.match_threshold:
            return best_incident, round(best_score, 2)

        return None, 0.0
