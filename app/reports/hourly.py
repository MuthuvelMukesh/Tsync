"""
Hourly intelligence briefing generator.
"""

from typing import Tuple
from app.reports.formatters import (
    format_plain_text,
    format_telegram_markdown,
    format_whatsapp_text,
)
from app.services.briefing_service import BriefingDigest


class HourlyReportGenerator:
    """Generates multi-channel formatted hourly briefings."""

    @staticmethod
    def generate(digest: BriefingDigest) -> Tuple[str, str, str]:
        """
        Returns:
            (plain_text, telegram_markdown, whatsapp_text)
        """
        text = format_plain_text(digest)
        tg = format_telegram_markdown(digest)
        wa = format_whatsapp_text(digest)
        return text, tg, wa
