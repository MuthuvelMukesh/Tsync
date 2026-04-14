"""
telegram_client.py — Telethon-based Telegram message collector.

Connects to Telegram using user client credentials,
fetches messages from configured channels, and stores them.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from telethon import TelegramClient
from telethon.errors import (
    ChannelPrivateError,
    ChannelInvalidError,
    FloodWaitError,
)
from dotenv import load_dotenv

from database import bulk_insert_messages

load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_NAME = "tsync_session"


def load_config() -> dict:
    """Load configuration from config.json."""
    with open("config.json", "r") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    """Save configuration to config.json."""
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)


def add_channel(channel: str) -> bool:
    """Add a channel to the watch list."""
    config = load_config()
    channel = channel.strip().lstrip("@")
    if channel in config["channels"]:
        print(f"[CONFIG] Channel '{channel}' already exists.")
        return False
    config["channels"].append(channel)
    save_config(config)
    print(f"[CONFIG] Added channel: {channel}")
    return True


def remove_channel(channel: str) -> bool:
    """Remove a channel from the watch list."""
    config = load_config()
    channel = channel.strip().lstrip("@")
    if channel not in config["channels"]:
        print(f"[CONFIG] Channel '{channel}' not found.")
        return False
    config["channels"].remove(channel)
    save_config(config)
    print(f"[CONFIG] Removed channel: {channel}")
    return True


def list_channels() -> list[str]:
    """List all configured channels."""
    config = load_config()
    channels = config.get("channels", [])
    print(f"[CONFIG] Configured channels ({len(channels)}):")
    for ch in channels:
        print(f"  - @{ch}")
    return channels


async def fetch_messages(
    client: TelegramClient,
    channel: str,
    limit: int = 100,
    hours_back: int = 24
) -> list[dict]:
    """
    Fetch recent messages from a channel.

    Args:
        client: Active TelegramClient
        channel: Channel username or ID
        limit: Maximum messages to fetch
        hours_back: How far back to look

    Returns:
        List of message dicts ready for storage
    """
    messages = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    try:
        entity = await client.get_entity(channel)
        print(f"[TELEGRAM] Fetching from @{channel}...")

        async for msg in client.iter_messages(entity, limit=limit):
            if msg.date < cutoff:
                break

            if not msg.text or len(msg.text.strip()) < 10:
                continue

            messages.append({
                "telegram_id": msg.id,
                "text": msg.text.strip(),
                "source_channel": channel,
                "date": msg.date.strftime("%Y-%m-%d"),
            })

        print(f"[TELEGRAM] Fetched {len(messages)} messages from @{channel}")

    except ChannelPrivateError:
        print(f"[TELEGRAM] Cannot access @{channel} — private channel.")
    except ChannelInvalidError:
        print(f"[TELEGRAM] Invalid channel: @{channel}")
    except FloodWaitError as e:
        print(f"[TELEGRAM] Rate limited. Wait {e.seconds}s")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        print(f"[TELEGRAM] Error fetching @{channel}: {e}")

    return messages


async def collect_all_messages() -> int:
    """
    Connect to Telegram, fetch from all configured channels,
    and store messages in the database.

    Returns:
        Total number of new messages stored.
    """
    if not API_ID or not API_HASH:
        print("[TELEGRAM] ERROR: Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env")
        return 0

    config = load_config()
    channels = config.get("channels", [])
    message_limit = config.get("message_limit", 100)

    if not channels:
        print("[TELEGRAM] No channels configured. Add channels to config.json")
        return 0

    total_stored = 0

    async with TelegramClient(SESSION_NAME, int(API_ID), API_HASH) as client:
        print("[TELEGRAM] Connected successfully.")

        for channel in channels:
            messages = await fetch_messages(
                client, channel, limit=message_limit
            )
            if messages:
                stored = bulk_insert_messages(messages)
                total_stored += stored
                print(f"[TELEGRAM] Stored {stored} new messages from @{channel}")

            # Small delay to avoid rate limits
            await asyncio.sleep(1)

    print(f"[TELEGRAM] Total new messages stored: {total_stored}")
    return total_stored
