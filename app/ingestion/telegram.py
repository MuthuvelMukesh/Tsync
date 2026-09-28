"""
Telegram message source implementation using Telethon.
Restricted exclusively to ingestion operations.
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional

from app.domain.messages import RawMessage
from app.ingestion.base import IngestionError, MessageSource


class TelegramMessageSource:
    """Telethon adapter implementing MessageSource protocol."""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        channels: List[str],
        session_name: str = "tsync_session",
        message_limit: int = 100,
    ):
        self.api_id = api_id
        self.api_hash = api_hash
        self.channels = [ch.strip().lstrip("@") for ch in channels]
        self.session_name = session_name
        self.message_limit = message_limit

    @property
    def source_name(self) -> str:
        return "telegram"

    async def fetch(
        self, start_time: datetime, end_time: datetime
    ) -> List[RawMessage]:
        """Fetch messages published between start_time and end_time."""
        if not self.api_id or not self.api_hash:
            print("[TELEGRAM_INGEST] Warning: Telegram credentials not provided, skipping Telegram fetch.")
            return []

        try:
            from telethon import TelegramClient
            from telethon.errors import (
                ChannelPrivateError,
                ChannelInvalidError,
                FloodWaitError,
            )
        except ImportError:
            raise IngestionError("Telethon is not installed.")

        raw_messages: List[RawMessage] = []

        try:
            async with TelegramClient(self.session_name, self.api_id, self.api_hash) as client:
                for channel in self.channels:
                    try:
                        entity = await client.get_entity(channel)
                        async for msg in client.iter_messages(entity, limit=self.message_limit):
                            if not msg.date:
                                continue

                            # Standardize to timezone-aware UTC
                            msg_dt = msg.date
                            if msg_dt.tzinfo is None:
                                msg_dt = msg_dt.replace(tzinfo=timezone.utc)

                            # Respect time boundaries
                            if msg_dt < start_time:
                                break
                            if msg_dt > end_time:
                                continue

                            if not msg.text or len(msg.text.strip()) < 10:
                                continue

                            raw_messages.append(
                                RawMessage(
                                    source_channel=channel,
                                    external_id=str(msg.id),
                                    text=msg.text.strip(),
                                    published_at=msg_dt,
                                    metadata={
                                        "sender_id": str(msg.sender_id),
                                        "views": getattr(msg, "views", 0),
                                        "forwards": getattr(msg, "forwards", 0),
                                    },
                                )
                            )
                    except ChannelPrivateError:
                        print(f"[TELEGRAM_INGEST] Cannot access private channel @{channel}")
                    except ChannelInvalidError:
                        print(f"[TELEGRAM_INGEST] Invalid channel @{channel}")
                    except FloodWaitError as e:
                        print(f"[TELEGRAM_INGEST] Rate limited. Waiting {e.seconds}s")
                        await asyncio.sleep(e.seconds)
                    except Exception as err:
                        print(f"[TELEGRAM_INGEST] Error fetching channel @{channel}: {err}")

                    await asyncio.sleep(0.5)

        except Exception as e:
            print(f"[TELEGRAM_INGEST] Telegram connection error: {e}")

        return raw_messages
