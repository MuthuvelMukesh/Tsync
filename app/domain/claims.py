"""
Domain models for claims and contradictions.
Independent of databases, frameworks, and third-party APIs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Claim:
    """A specific factual assertion made in a message or report."""
    id: Optional[int]
    incident_id: Optional[int]
    message_id: Optional[int]
    statement: str
    source_name: str
    confidence: float = 0.5
    is_disputed: bool = False
    extracted_at: Optional[datetime] = None


@dataclass
class Contradiction:
    """A detected contradiction between two claims or reports."""
    claim_a: Claim
    claim_b: Claim
    explanation: str
    severity: str = "medium"  # low, medium, high
    detected_at: Optional[datetime] = None
