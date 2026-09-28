"""
Notification dispatcher coordinating delivery across providers and evaluating policy.
"""

from typing import Dict, List, Optional
from app.domain.events import (
    DomainEvent,
    IncidentCreated,
    IncidentUpdated,
    BreakingIncidentDetected,
)
from app.domain.incidents import Incident
from app.notifications.base import (
    NotificationPolicy,
    NotificationProvider,
    NotificationResult,
)
from app.storage.repositories.notifications import NotificationAuditRepository


class NotificationDispatcher:
    """Dispatches notifications according to policy and records audit logs."""

    def __init__(
        self,
        providers: List[NotificationProvider],
        policy: Optional[NotificationPolicy] = None,
        audit_repo: Optional[NotificationAuditRepository] = None,
        default_telegram_chat_id: str = "",
        default_whatsapp_phone: str = "",
    ):
        self.providers: Dict[str, NotificationProvider] = {
            p.channel_name: p for p in providers
        }
        self.policy = policy or NotificationPolicy()
        self.audit_repo = audit_repo
        self.default_telegram_chat_id = default_telegram_chat_id
        self.default_whatsapp_phone = default_whatsapp_phone

    async def handle_domain_event(self, event: DomainEvent) -> List[NotificationResult]:
        """Evaluate policy and dispatch notification if warranted."""
        if not self.policy.should_notify(event):
            return []

        results: List[NotificationResult] = []

        if isinstance(event, BreakingIncidentDetected):
            inc = event.incident
            msg = (
                f"🚨 *BREAKING INTEL ALERT*\n\n"
                f"*{inc.title}*\n"
                f"Severity: {inc.severity.value} | Category: {inc.category.title()}\n"
                f"Score: {inc.importance_score:.1f}/10\n\n"
                f"Summary: {inc.summary}\n\n"
                f"Sources: {', '.join(['@' + s for s in inc.sources])}"
            )
            results = await self.broadcast(msg, event_type="breaking_alert")

        elif isinstance(event, (IncidentCreated, IncidentUpdated)):
            inc = event.incident
            action = "NEW INCIDENT" if isinstance(event, IncidentCreated) else "MATERIAL UPDATE"
            msg = (
                f"⚡ *{action}: {inc.title}*\n"
                f"Status: {inc.status.value} | Severity: {inc.severity.value}\n"
                f"Score: {inc.importance_score:.1f}/10\n\n"
                f"{inc.summary}\n\n"
                f"Why it matters: {inc.why_it_matters}"
            )
            results = await self.broadcast(msg, event_type="material_update")

        return results

    async def broadcast(self, message: str, event_type: str = "broadcast") -> List[NotificationResult]:
        """Broadcast message to all active channel destinations."""
        results: List[NotificationResult] = []

        # Telegram
        if "telegram" in self.providers and self.default_telegram_chat_id:
            res = await self.providers["telegram"].send(
                self.default_telegram_chat_id, message
            )
            results.append(res)
            if self.audit_repo:
                await self.audit_repo.record(
                    event_type=event_type,
                    recipient=self.default_telegram_chat_id,
                    channel="telegram",
                    message_payload=message,
                    status="sent" if res.success else "failed",
                    error=res.error,
                )

        # WhatsApp
        if "whatsapp" in self.providers and self.default_whatsapp_phone:
            res = await self.providers["whatsapp"].send(
                self.default_whatsapp_phone, message
            )
            results.append(res)
            if self.audit_repo:
                await self.audit_repo.record(
                    event_type=event_type,
                    recipient=self.default_whatsapp_phone,
                    channel="whatsapp",
                    message_payload=message,
                    status="sent" if res.success else "failed",
                    error=res.error,
                )

        return results

    async def send_to_channel(
        self, channel_name: str, recipient: str, message: str, event_type: str = "direct"
    ) -> NotificationResult:
        """Send message to a specific provider."""
        provider = self.providers.get(channel_name)
        if not provider:
            return NotificationResult(
                success=False,
                channel=channel_name,
                recipient=recipient,
                error=f"Provider '{channel_name}' not registered.",
            )

        res = await provider.send(recipient, message)
        if self.audit_repo:
            await self.audit_repo.record(
                event_type=event_type,
                recipient=recipient,
                channel=channel_name,
                message_payload=message,
                status="sent" if res.success else "failed",
                error=res.error,
            )
        return res
