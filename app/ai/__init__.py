"""
AI module providing provider protocol, schemas, retries, and OpenRouter integration.
"""

from app.ai.base import AIProvider, AIProviderError, RateLimitError
from app.ai.models import (
    ClassificationResult,
    SummaryResult,
    IncidentAnalysisResult,
    ClaimExtractionResult,
    QAResult,
)
from app.ai.openrouter import OpenRouterAIProvider
from app.ai.retry import async_retry

__all__ = [
    "AIProvider",
    "AIProviderError",
    "RateLimitError",
    "ClassificationResult",
    "SummaryResult",
    "IncidentAnalysisResult",
    "ClaimExtractionResult",
    "QAResult",
    "OpenRouterAIProvider",
    "async_retry",
]
