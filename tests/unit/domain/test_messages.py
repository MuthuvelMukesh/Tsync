"""
Unit tests for domain messages.
"""

from datetime import datetime, timezone
from app.domain.messages import Message, RawMessage, MessageFilterResult


def test_raw_message_creation():
    now = datetime.now(timezone.utc)
    raw = RawMessage(
        source_channel="tech",
        external_id="123",
        text="Sample text",
        published_at=now,
    )
    assert raw.source_channel == "tech"
    assert raw.external_id == "123"


def test_message_breaking_property():
    now = datetime.now(timezone.utc)
    msg_normal = Message(
        id=1,
        external_id="1",
        source_channel="c",
        text="t",
        cleaned_text="t",
        published_at=now,
        importance_score=6.5,
    )
    assert not msg_normal.is_breaking

    msg_breaking = Message(
        id=2,
        external_id="2",
        source_channel="c",
        text="t",
        cleaned_text="t",
        published_at=now,
        importance_score=8.7,
    )
    assert msg_breaking.is_breaking
