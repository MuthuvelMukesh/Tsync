"""
Unit tests for incident clustering.
"""

from datetime import datetime, timezone
from app.domain.messages import Message
from app.incidents.clustering import IncidentClusterer


def test_cluster_messages():
    clusterer = IncidentClusterer(similarity_threshold=0.25)
    now = datetime.now(timezone.utc)

    m1 = Message(1, "1", "c", "NVIDIA launches Blackwell GPU", "NVIDIA launches Blackwell GPU", now, category="tech")
    m2 = Message(2, "2", "c", "NVIDIA Blackwell GPU architecture details", "NVIDIA Blackwell GPU architecture details", now, category="tech")
    m3 = Message(3, "3", "c", "Federal Reserve interest rate cuts expected", "Federal Reserve interest rate cuts expected", now, category="finance")

    clusters = clusterer.cluster_messages([m1, m2, m3])
    assert len(clusters) == 2
    # m1 and m2 should be in one cluster
    assert len(clusters[0]) == 2 or len(clusters[1]) == 2
