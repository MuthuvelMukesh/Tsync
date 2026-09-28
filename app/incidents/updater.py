"""
Incident updater managing status transitions, importance score updates, and material change detection.
"""

from datetime import datetime, timezone
from typing import Tuple

from app.domain.incidents import Incident, IncidentSeverity, IncidentStatus
from app.domain.messages import Message


class IncidentUpdater:
    """Updates an existing incident with new message data and assesses material impact."""

    def update_incident(
        self, incident: Incident, message: Message
    ) -> Tuple[Incident, bool, str]:
        """
        Merge new message into incident.
        Returns: (updated_incident, is_material_change, change_summary)
        """
        old_score = incident.importance_score
        old_severity = incident.severity
        material_reasons = []

        # 1. Update sources
        new_source = incident.add_source(message.source_channel)
        if new_source:
            material_reasons.append(f"Corroborated by new source @{message.source_channel}")

        # 2. Update importance score
        if message.importance_score > incident.importance_score:
            score_delta = message.importance_score - incident.importance_score
            incident.importance_score = max(incident.importance_score, message.importance_score)
            if score_delta >= 1.5:
                material_reasons.append(f"Importance increased by {score_delta:.1f}")

        # 3. Recompute severity
        incident.recompute_severity()
        if incident.severity != old_severity:
            material_reasons.append(
                f"Severity escalated from {old_severity.value} to {incident.severity.value}"
            )

        # 4. Status progression
        if incident.status == IncidentStatus.NEW and len(incident.sources) >= 2:
            if incident.can_transition_to(IncidentStatus.DEVELOPING):
                incident.transition_to(IncidentStatus.DEVELOPING, "Multi-source confirmation")
                material_reasons.append("Status progressed to DEVELOPING")

        # 5. Check if breaking
        if message.is_breaking and not (old_score >= 8.5):
            material_reasons.append("Breaking alert triggered")

        incident.updated_at = datetime.now(timezone.utc)
        is_material = len(material_reasons) > 0
        change_summary = "; ".join(material_reasons) if is_material else "Routine update"

        return incident, is_material, change_summary
