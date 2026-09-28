"""
Ingestion module for collecting raw messages from external sources.
"""

from app.ingestion.base import MessageSource, IngestionStats, IngestionError
from app.ingestion.telegram import TelegramMessageSource
from app.ingestion.service import IngestionService

__all__ = [
    "MessageSource",
    "IngestionStats",
    "IngestionError",
    "TelegramMessageSource",
    "IngestionService",
]
