"""
Ingestion abstractions and MessageSource protocol.
Isolates ingestion protocols from specific providers (Telegram, RSS, Mock).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Protocol
from app.domain.messages import RawMessage


class IngestionError(Exception):
    """Base exception for data source ingestion failures."""
    pass


@dataclass
class IngestionStats:
    """Summary of messages collected during an ingestion cycle."""
    source_name: str
    total_fetched: int
    new_stored: int
    skipped_duplicates: int
    duration_seconds: float = 0.0


class MessageSource(Protocol):
    """Protocol for any incoming intelligence data source."""

    @property
    def source_name(self) -> str:
        """Identifier for this source (e.g. 'telegram', 'rss_reuters')."""
        ...

    async def fetch(
        self, start_time: datetime, end_time: datetime
    ) -> List[RawMessage]:
        """Collect messages published within the given time range."""
        ...
