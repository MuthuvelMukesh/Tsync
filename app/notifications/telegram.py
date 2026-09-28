"""
Telegram bot notification provider implementation.
Delivers messages to configured Telegram channels or chat IDs.
"""

from typing import Optional
import httpx

from app.notifications.base import (
    NotificationDeliveryError,
    NotificationProvider,
    NotificationResult,
)


class TelegramNotificationProvider:
    """Delivers alerts and digests via Telegram Bot HTTP API."""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    @property
    def channel_name(self) -> str:
        return "telegram"

    async def send(self, recipient: str, message: str) -> NotificationResult:
        if not self.bot_token:
            return NotificationResult(
                success=False,
                channel=self.channel_name,
                recipient=recipient,
                error="Telegram Bot Token not configured.",
            )

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": recipient,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                if resp.is_error:
                    # Retry without markdown if parsing failed
                    if "can't parse entities" in resp.text:
                        payload.pop("parse_mode")
                        resp = await client.post(url, json=payload)

                if resp.is_error:
                    return NotificationResult(
                        success=False,
                        channel=self.channel_name,
                        recipient=recipient,
                        error=f"Telegram API HTTP {resp.status_code}: {resp.text}",
                    )

                data = resp.json()
                msg_id = str(data.get("result", {}).get("message_id", ""))
                return NotificationResult(
                    success=True,
                    channel=self.channel_name,
                    recipient=recipient,
                    external_message_id=msg_id,
                )
        except Exception as e:
            return NotificationResult(
                success=False,
                channel=self.channel_name,
                recipient=recipient,
                error=str(e),
            )
