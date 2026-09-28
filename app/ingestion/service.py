"""
Ingestion service coordinating multiple sources and message persistence.
"""

from datetime import datetime, timezone
import time
from typing import List

from app.domain.messages import Message, RawMessage
from app.ingestion.base import IngestionStats, MessageSource
from app.processing.filtering import filter_raw_message
from app.processing.normalization import clean_text
from app.storage.repositories.messages import MessageRepository


class IngestionService:
    """Orchestrates message collection across registered MessageSources."""

    def __init__(
        self,
        message_repo: MessageRepository,
        sources: List[MessageSource],
    ):
        self.message_repo = message_repo
        self.sources = sources

    async def ingest_all(
        self, start_time: datetime, end_time: datetime
    ) -> List[IngestionStats]:
        """Run ingestion across all configured sources."""
        stats_list: List[IngestionStats] = []

        for source in self.sources:
            start_ts = time.time()
            try:
                raw_messages = await source.fetch(start_time=start_time, end_time=end_time)
                new_saved = 0
                duplicates = 0

                domain_messages: List[Message] = []
                for raw in raw_messages:
                    filter_res = filter_raw_message(raw)
                    if filter_res.should_skip:
                        continue

                    # Check for existence
                    existing = await self.message_repo.get_by_source_and_external_id(
                        source_channel=raw.source_channel,
                        external_id=raw.external_id,
                    )
                    if existing:
                        duplicates += 1
                        continue

                    msg = Message(
                        id=None,
                        external_id=raw.external_id,
                        source_channel=raw.source_channel,
                        text=raw.text,
                        cleaned_text=clean_text(raw.text),
                        published_at=raw.published_at,
                        category="uncategorized",
                        created_at=datetime.now(timezone.utc),
                    )
                    domain_messages.append(msg)

                if domain_messages:
                    saved = await self.message_repo.bulk_create(domain_messages)
                    new_saved = len(saved)

                duration = time.time() - start_ts
                stats_list.append(
                    IngestionStats(
                        source_name=source.source_name,
                        total_fetched=len(raw_messages),
                        new_stored=new_saved,
                        skipped_duplicates=duplicates,
                        duration_seconds=round(duration, 2),
                    )
                )

            except Exception as e:
                print(f"[INGEST_SERVICE] Failed ingestion for source {source.source_name}: {e}")
                stats_list.append(
                    IngestionStats(
                        source_name=source.source_name,
                        total_fetched=0,
                        new_stored=0,
                        skipped_duplicates=0,
                        duration_seconds=round(time.time() - start_ts, 2),
                    )
                )

        return stats_list
