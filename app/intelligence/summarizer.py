"""
Intelligence summarizer producing structured headlines, summaries, and impacts.
"""

from typing import Optional
from app.ai.base import AIProvider
from app.ai.models import SummaryResult


class IntelligenceSummarizer:
    """Generates structured intelligence using an AI provider with robust fallback."""

    def __init__(self, ai_provider: Optional[AIProvider] = None):
        self._ai_provider = ai_provider

    async def summarize(self, text: str, category: str = "other") -> SummaryResult:
        if self._ai_provider:
            try:
                return await self._ai_provider.summarize(text=text, category=category)
            except Exception as e:
                print(f"[SUMMARIZER] AI provider failed, falling back to heuristics: {e}")

        # Heuristic fallback
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        first_line = lines[0] if lines else "Intelligence Update"
        headline = first_line[:90] + ("..." if len(first_line) > 90 else "")

        summary = text[:250] + ("..." if len(text) > 250 else "")
        why = f"High-significance update detected in category '{category}'."

        return SummaryResult(
            headline=headline,
            summary=summary,
            why_it_matters=why,
        )
