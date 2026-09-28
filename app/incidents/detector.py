"""
Incident detector determining whether incoming messages qualify as trackable incidents.
"""

from app.domain.messages import Message


class IncidentDetector:
    """Evaluates whether messages meet the threshold to trigger or update an incident."""

    def __init__(self, min_incident_score: float = 5.0):
        self.min_incident_score = min_incident_score

    def should_track_as_incident(self, message: Message) -> bool:
        """
        Check if message importance and content warrant incident tracking.
        Messages with high importance scores (>= 5.0) or breaking indicators qualify.
        """
        if message.importance_score >= self.min_incident_score:
            return True

        if message.is_breaking:
            return True

        return False
