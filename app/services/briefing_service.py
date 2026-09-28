"""
Briefing service for generating executive digests, trend detection, and intensity metrics.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Dict, List

from app.domain.incidents import Incident

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
}


@dataclass
class TrendTopic:
    topic: str
    count: int
    relevance_score: float


@dataclass
class BriefingDigest:
    """Consolidated briefing report data."""
    period: str  # "hourly" | "daily"
    generated_at: datetime
    total_incidents: int
    breaking_count: int
    intensity: str  # "LOW" | "MEDIUM" | "HIGH"
    incidents: List[Incident]
    category_distribution: Dict[str, int]
    trends: List[TrendTopic]
    patterns: List[str]


class BriefingService:
    """Generates structured digests and analytical metrics from incident domain objects."""

    @staticmethod
    def calculate_intensity(total_count: int, avg_score: float) -> str:
        """Derive overall operational intensity."""
        if total_count >= 10 or avg_score >= 7.5:
            return "HIGH"
        elif total_count >= 4 or avg_score >= 5.0:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def extract_trends(incidents: List[Incident], top_n: int = 6) -> List[TrendTopic]:
        """Extract dominant n-gram topics across incident titles and summaries."""
        if not incidents:
            return []

        full_text = " ".join(f"{i.title} {i.summary}" for i in incidents)
        clean = re.sub(r"[^\w\s]", " ", full_text.lower())
        words = [w for w in clean.split() if w not in STOP_WORDS and len(w) > 2]

        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
        counts = Counter(bigrams)

        topics: List[TrendTopic] = []
        for topic, count in counts.most_common(top_n):
            if count >= 1:
                rel = round((count / len(incidents)) * 10, 1)
                topics.append(TrendTopic(topic=topic.title(), count=count, relevance_score=rel))

        return topics

    @staticmethod
    def detect_patterns(incidents: List[Incident]) -> List[str]:
        """Detect macro themes across current incidents."""
        patterns: List[str] = []
        if not incidents:
            return patterns

        categories = Counter(i.category for i in incidents)
        for cat, cnt in categories.items():
            if cnt / len(incidents) >= 0.4:
                patterns.append(f"Significant cluster in {cat.title()} ({cnt} active incidents)")

        breaking = [i for i in incidents if i.is_breaking]
        if breaking:
            patterns.append(f"{len(breaking)} breaking / critical developments active")

        multi_source = [i for i in incidents if len(i.sources) >= 2]
        if multi_source:
            patterns.append(f"{len(multi_source)} incidents corroborated by multiple channels")

        return patterns

    def generate_digest(
        self, incidents: List[Incident], period: str = "hourly"
    ) -> BriefingDigest:
        """Compile a complete briefing digest from a list of incidents."""
        now = datetime.now()
        categories = dict(Counter(i.category for i in incidents).most_common())
        breaking_cnt = sum(1 for i in incidents if i.is_breaking)
        avg_score = (
            sum(i.importance_score for i in incidents) / len(incidents)
            if incidents else 0.0
        )
        intensity = self.calculate_intensity(len(incidents), avg_score)
        trends = self.extract_trends(incidents)
        patterns = self.detect_patterns(incidents)

        # Sort incidents with breaking and highest score first
        sorted_incidents = sorted(
            incidents,
            key=lambda x: (x.is_breaking, x.importance_score),
            reverse=True,
        )

        return BriefingDigest(
            period=period,
            generated_at=now,
            total_incidents=len(incidents),
            breaking_count=breaking_cnt,
            intensity=intensity,
            incidents=sorted_incidents,
            category_distribution=categories,
            trends=trends,
            patterns=patterns,
        )
