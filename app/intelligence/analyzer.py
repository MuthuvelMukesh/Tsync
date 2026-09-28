"""
Incident analyzer orchestrating AI analysis and strategic synthesis.
"""

from typing import Optional
from app.ai.base import AIProvider
from app.ai.models import IncidentAnalysisResult
from app.domain.incidents import Incident
from app.domain.messages import Message


class IncidentAnalyzer:
    """Analyzes incidents and updates using an AI provider."""

    def __init__(self, ai_provider: Optional[AIProvider] = None):
        self._ai_provider = ai_provider

    async def analyze(
        self, incident: Incident, latest_message: Message
    ) -> IncidentAnalysisResult:
        context = f"Category: {incident.category}\nCurrent Summary: {incident.summary}\nPrior Sources: {', '.join(incident.sources)}"

        if self._ai_provider:
            try:
                return await self._ai_provider.analyze_incident(
                    title=incident.title,
                    text=latest_message.cleaned_text,
                    context=context,
                )
            except Exception as e:
                print(f"[ANALYZER] AI provider error, using fallback: {e}")

        # Local fallback synthesis
        return IncidentAnalysisResult(
            title=incident.title or latest_message.headline or "Incident Update",
            summary=latest_message.summary or latest_message.cleaned_text[:300],
            key_developments=[latest_message.cleaned_text[:150]],
            strategic_implications=latest_message.why_it_matters or "Ongoing situation under observation.",
            confidence=incident.confidence_score,
            suggested_severity=incident.severity.value,
        )
