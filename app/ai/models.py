"""
Data models and schemas for AI inputs and outputs.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    """Result of categorizing a message."""
    category: str = Field(description="Assigned category name")
    confidence: float = Field(default=0.8, description="Classification confidence (0.0 to 1.0)")


class SummaryResult(BaseModel):
    """Structured intelligence summary (What + Why)."""
    headline: str = Field(description="Concise, impactful headline (max 15 words)")
    summary: str = Field(description="What happened — factual summary in 2-3 sentences")
    why_it_matters: str = Field(description="Why this matters — impact and implications")


class IncidentAnalysisResult(BaseModel):
    """In-depth analysis of an unfolding incident."""
    title: str = Field(description="Standardized incident title")
    summary: str = Field(description="Synthesized overview")
    key_developments: List[str] = Field(default_factory=list, description="Key timeline bullets")
    strategic_implications: str = Field(default="", description="Strategic implications")
    confidence: float = Field(default=0.7, description="Overall confidence assessment")
    suggested_severity: str = Field(default="MEDIUM", description="Suggested incident severity")


class ClaimExtractionResult(BaseModel):
    """Factual assertions extracted from text."""
    claims: List[str] = Field(default_factory=list, description="Extracted claim statements")


class QAResult(BaseModel):
    """Answer to user intelligence query."""
    answer: str = Field(description="Factual answer based on context")
    confidence: float = Field(default=0.8, description="Confidence in the answer")
