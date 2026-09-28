"""
SQLAlchemy ORM models for Tsync storage layer.
"""

from datetime import datetime, timezone
import json
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.database import Base


class MessageModel(Base):
    """Stores incoming messages and their processing results."""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_channel: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_text: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), default="uncategorized", index=True)
    importance_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    headline: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    why_it_matters: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    incident_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    incident: Mapped[Optional["IncidentModel"]] = relationship("IncidentModel", back_populates="messages")

    __table_args__ = (
        Index("idx_source_external", "source_channel", "external_id", unique=True),
    )


class IncidentModel(Base):
    """Stores detected and aggregated incidents."""
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="NEW", index=True)
    severity: Mapped[str] = mapped_column(String(32), default="LOW", index=True)
    importance_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    summary: Mapped[str] = mapped_column(Text, default="")
    why_it_matters: Mapped[str] = mapped_column(Text, default="")
    sources_json: Mapped[str] = mapped_column(Text, default="[]")
    contradictions_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    messages: Mapped[List["MessageModel"]] = relationship(
        "MessageModel", back_populates="incident", lazy="selectin"
    )
    timeline: Mapped[List["TimelineModel"]] = relationship(
        "TimelineModel", back_populates="incident", cascade="all, delete-orphan", lazy="selectin"
    )
    claims: Mapped[List["ClaimModel"]] = relationship(
        "ClaimModel", back_populates="incident", cascade="all, delete-orphan", lazy="selectin"
    )
    entities: Mapped[List["EntityModel"]] = relationship(
        "EntityModel", back_populates="incident", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def sources_list(self) -> List[str]:
        try:
            return json.loads(self.sources_json)
        except Exception:
            return []

    @sources_list.setter
    def sources_list(self, value: List[str]) -> None:
        self.sources_json = json.dumps(list(set(value)))


class TimelineModel(Base):
    """Chronological event log for an incident."""
    __tablename__ = "incident_timeline"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_channel: Mapped[str] = mapped_column(String(128), default="")
    importance_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_major_event: Mapped[bool] = mapped_column(Boolean, default=False)
    message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    incident: Mapped["IncidentModel"] = relationship("IncidentModel", back_populates="timeline")


class ClaimModel(Base):
    """Extracted claims associated with an incident."""
    __tablename__ = "incident_claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str] = mapped_column(String(128), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    is_disputed: Mapped[bool] = mapped_column(Boolean, default=False)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    incident: Mapped["IncidentModel"] = relationship("IncidentModel", back_populates="claims")


class EntityModel(Base):
    """Named entities linked to incidents."""
    __tablename__ = "incident_entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), default="other")
    normalized_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0)

    incident: Mapped["IncidentModel"] = relationship("IncidentModel", back_populates="entities")


class SourceModel(Base):
    """Managed ingestion sources (Telegram channels, RSS feeds, etc.)."""
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username_or_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(128), default="")
    source_type: Mapped[str] = mapped_column(String(32), default="telegram")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_polled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationAuditModel(Base):
    """Audit log of delivered notifications."""
    __tablename__ = "notification_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    recipient: Mapped[str] = mapped_column(String(128), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)  # telegram, whatsapp
    message_payload: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="sent")  # sent, failed, skipped
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
