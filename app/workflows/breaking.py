"""
Breaking workflow for immediate high-urgency message evaluation and instant alert dispatch.
"""

from typing import List
from app.domain.messages import Message
from app.notifications.dispatcher import NotificationDispatcher
from app.services.incident_service import IncidentService


async def run_breaking_workflow(
    incoming_messages: List[Message],
    incident_service: IncidentService,
    notification_dispatcher: NotificationDispatcher,
) -> int:
    """
    Evaluates messages for immediate breaking triggers and ensures rapid alerting.
    Returns the count of breaking alerts triggered.
    """
    breaking_triggered = 0

    for msg in incoming_messages:
        if msg.importance_score >= 8.5 or msg.is_breaking:
            res = await incident_service.process_message(msg)
            if res and (res.incident.is_breaking or res.is_material_change):
                breaking_triggered += 1

    return breaking_triggered
