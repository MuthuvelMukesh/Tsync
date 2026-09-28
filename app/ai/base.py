"""
Base AI provider protocol and interfaces.
Enables pluggable AI backends (OpenRouter, local models, mock providers).
"""

from typing import List, Protocol
from app.ai.models import (
    ClassificationResult,
    SummaryResult,
    IncidentAnalysisResult,
    ClaimExtractionResult,
    QAResult,
)


class AIProviderError(Exception):
    """Base exception for all AI provider operations."""
    pass


class RateLimitError(AIProviderError):
    """Raised when provider rate limits are encountered."""
    pass


class AIProvider(Protocol):
    """Protocol defining the standard AI operations required by Tsync."""

    async def classify(self, text: str) -> ClassificationResult:
        """Classify message text into a predefined category."""
        ...

    async def summarize(self, text: str, category: str) -> SummaryResult:
        """Generate structured intelligence: headline, summary, and why it matters."""
        ...

    async def analyze_incident(
        self, title: str, text: str, context: str = ""
    ) -> IncidentAnalysisResult:
        """Perform comprehensive intelligence synthesis for an incident."""
        ...

    async def extract_claims(self, text: str) -> ClaimExtractionResult:
        """Extract key verifiable claims from news or message text."""
        ...

    async def answer_question(self, question: str, context: str) -> QAResult:
        """Answer an analytical query given incident context."""
        ...
