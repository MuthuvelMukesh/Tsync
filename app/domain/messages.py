"""
Domain models for messages.
Independent of databases, frameworks, and third-party APIs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class RawMessage:
    """Unprocessed incoming message from an external source."""
    source_channel: str
    external_id: str
    text: str
    published_at: datetime
    metadata: dict = field(default_factory=dict)


@dataclass
class MessageFilterResult:
    """Result of filtering a message before processing."""
    should_skip: bool
    reason: Optional[str] = None
    rule_category: Optional[str] = None
    rule_confidence: float = 0.0
    needs_ai_fallback: bool = False


@dataclass
class Message:
    """Normalized and processed domain message."""
    id: Optional[int]
    external_id: str
    source_channel: str
    text: str
    cleaned_text: str
    published_at: datetime
    category: str = "uncategorized"
    importance_score: float = 0.0
    is_selected: bool = False
    headline: Optional[str] = None
    summary: Optional[str] = None
    why_it_matters: Optional[str] = None
    incident_id: Optional[int] = None
    created_at: Optional[datetime] = None

    @property
    def is_breaking(self) -> bool:
        if self.importance_score >= 8.5:
            return True
        if self.text and self.text.strip().upper().startswith("BREAKING"):
            return True
        return False
