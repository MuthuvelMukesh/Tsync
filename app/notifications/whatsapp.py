"""
WhatsApp Cloud API notification provider implementation.
Encapsulates all Meta Graph API interactions.
"""

from typing import Optional
import httpx

from app.notifications.base import (
    NotificationDeliveryError,
    NotificationProvider,
    NotificationResult,
)


class WhatsAppNotificationProvider:
    """Delivers messages via WhatsApp Cloud API."""

    def __init__(
        self,
        access_token: str,
        phone_number_id: str,
        api_version: str = "v19.0",
    ):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.api_version = api_version

    @property
    def channel_name(self) -> str:
        return "whatsapp"

    async def send(self, recipient: str, message: str) -> NotificationResult:
        if not self.access_token or not self.phone_number_id:
            return NotificationResult(
                success=False,
                channel=self.channel_name,
                recipient=recipient,
                error="WhatsApp credentials not configured.",
            )

        clean_recipient = recipient.strip().lstrip("+")
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_recipient,
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.is_error:
                    return NotificationResult(
                        success=False,
                        channel=self.channel_name,
                        recipient=clean_recipient,
                        error=f"WhatsApp API HTTP {resp.status_code}: {resp.text}",
                    )
                data = resp.json()
                msg_id = None
                if "messages" in data and len(data["messages"]) > 0:
                    msg_id = data["messages"][0].get("id")
                return NotificationResult(
                    success=True,
                    channel=self.channel_name,
                    recipient=clean_recipient,
                    external_message_id=msg_id,
                )
        except Exception as e:
            return NotificationResult(
                success=False,
                channel=self.channel_name,
                recipient=clean_recipient,
                error=str(e),
            )
