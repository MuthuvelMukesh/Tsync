"""
Intelligence layer: summarization, confidence scoring, entity extraction, and analysis.
"""

from app.intelligence.confidence import ConfidenceCalculator
from app.intelligence.entities import EntityExtractor
from app.intelligence.summarizer import IntelligenceSummarizer
from app.intelligence.analyzer import IncidentAnalyzer
from app.intelligence.prompts import (
    CLASSIFICATION_PROMPT_TEMPLATE,
    SUMMARIZE_PROMPT_TEMPLATE,
    INCIDENT_ANALYSIS_PROMPT_TEMPLATE,
    CLAIM_EXTRACTION_PROMPT_TEMPLATE,
    QA_PROMPT_TEMPLATE,
)

__all__ = [
    "ConfidenceCalculator",
    "EntityExtractor",
    "IntelligenceSummarizer",
    "IncidentAnalyzer",
    "CLASSIFICATION_PROMPT_TEMPLATE",
    "SUMMARIZE_PROMPT_TEMPLATE",
    "INCIDENT_ANALYSIS_PROMPT_TEMPLATE",
    "CLAIM_EXTRACTION_PROMPT_TEMPLATE",
    "QA_PROMPT_TEMPLATE",
]
