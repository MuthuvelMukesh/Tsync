"""
Global pytest configuration and fixtures for Tsync test suite.
"""

from datetime import datetime, timezone
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.storage.database import Base
from app.domain.messages import Message, RawMessage
from app.domain.incidents import Incident, IncidentStatus, IncidentSeverity
from app.domain.entities import NamedEntity, EntityType


@pytest_asyncio.fixture
async def async_db_session():
    """In-memory SQLite async session fixture for integration tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield session_factory

    await engine.dispose()


@pytest.fixture
def sample_raw_message() -> RawMessage:
    return RawMessage(
        source_channel="tech_channel",
        external_id="msg-101",
        text="BREAKING: OpenAI announces GPT-5 with revolutionary reasoning and multimodal systems.",
        published_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_domain_message() -> Message:
    return Message(
        id=1,
        external_id="msg-101",
        source_channel="tech_channel",
        text="BREAKING: OpenAI announces GPT-5 with revolutionary reasoning and multimodal systems.",
        cleaned_text="BREAKING: OpenAI announces GPT-5 with revolutionary reasoning and multimodal systems.",
        published_at=datetime.now(timezone.utc),
        category="technology",
        importance_score=8.8,
        is_selected=True,
        headline="OpenAI Announces GPT-5",
        summary="OpenAI has announced GPT-5 with high reasoning performance.",
        why_it_matters="Significant leap forward in frontier AI models.",
    )


@pytest.fixture
def sample_incident() -> Incident:
    return Incident(
        id=10,
        title="OpenAI Unveils GPT-5",
        category="technology",
        status=IncidentStatus.NEW,
        severity=IncidentSeverity.CRITICAL,
        importance_score=8.8,
        confidence_score=0.6,
        summary="Frontier AI model release with multimodal capabilities.",
        why_it_matters="Accelerates enterprise AI transformation.",
        sources=["tech_channel"],
        entities=[
            NamedEntity(name="OpenAI", entity_type=EntityType.ORGANIZATION, normalized_name="openai")
        ],
    )
