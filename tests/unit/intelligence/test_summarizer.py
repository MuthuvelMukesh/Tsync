"""
Unit tests for intelligence summarizer.
"""

import pytest
from app.ai.models import SummaryResult
from app.intelligence.summarizer import IntelligenceSummarizer


class MockAIProvider:
    async def summarize(self, text: str, category: str) -> SummaryResult:
        return SummaryResult(
            headline="Mock Headline",
            summary="Mock factual summary.",
            why_it_matters="Mock impact statement.",
        )


@pytest.mark.asyncio
async def test_summarizer_with_provider():
    summarizer = IntelligenceSummarizer(ai_provider=MockAIProvider())
    res = await summarizer.summarize("Sample text about energy sector", "finance")
    assert res.headline == "Mock Headline"
    assert res.summary == "Mock factual summary."


@pytest.mark.asyncio
async def test_summarizer_heuristic_fallback():
    summarizer = IntelligenceSummarizer(ai_provider=None)
    text = "First line breaking news announcement.\nSecond line details on the agreement."
    res = await summarizer.summarize(text, "technology")
    assert "First line breaking news" in res.headline
    assert "Second line" in res.summary
