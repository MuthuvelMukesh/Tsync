"""
Incident clustering for grouping messages into thematic incident clusters.
"""

from typing import Dict, List
from app.domain.messages import Message
from app.processing.normalization import compute_jaccard_similarity


class IncidentClusterer:
    """Clusters messages based on lexical and temporal similarity."""

    def __init__(self, similarity_threshold: float = 0.25):
        self.similarity_threshold = similarity_threshold

    def cluster_messages(self, messages: List[Message]) -> List[List[Message]]:
        """Group list of messages into related clusters."""
        if not messages:
            return []

        clusters: List[List[Message]] = []

        for msg in messages:
            assigned = False
            for cluster in clusters:
                # Check similarity against cluster centroid (first message)
                representative = cluster[0]
                if msg.category == representative.category:
                    sim = compute_jaccard_similarity(
                        msg.cleaned_text, representative.cleaned_text
                    )
                    if sim >= self.similarity_threshold:
                        cluster.append(msg)
                        assigned = True
                        break

            if not assigned:
                clusters.append([msg])

        return clusters
