"""
Incident repository protocol and SQLAlchemy implementation.
Maps between domain Incident models and database records.
"""

from datetime import datetime, timezone
import json
from typing import List, Optional, Protocol
from sqlalchemy import or_, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.incidents import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    TimelineEntry,
)
from app.domain.messages import Message
from app.domain.entities import NamedEntity, EntityType
from app.domain.claims import Claim
from app.storage.models import (
    ClaimModel,
    EntityModel,
    IncidentModel,
    TimelineModel,
)


class IncidentRepository(Protocol):
    """Abstract interface for incident storage."""

    async def get(self, incident_id: int) -> Optional[Incident]:
        ...

    async def create(self, incident: Incident) -> Incident:
        ...

    async def update(self, incident: Incident) -> Incident:
        ...

    async def find_candidates(self, message: Message) -> List[Incident]:
        ...

    async def list_active(self) -> List[Incident]:
        ...

    async def list_by_status(self, status: IncidentStatus) -> List[Incident]:
        ...

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> List[Incident]:
        ...

    async def add_timeline_entry(self, entry: TimelineEntry) -> TimelineEntry:
        ...

    async def add_claim(self, claim: Claim) -> Claim:
        ...


class SQLAlchemyIncidentRepository:
    """SQLAlchemy implementation of IncidentRepository with eager relationship loading."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _eager_options():
        return [
            selectinload(IncidentModel.timeline),
            selectinload(IncidentModel.claims),
            selectinload(IncidentModel.entities),
        ]

    @staticmethod
    def _ensure_tz(dt: Optional[datetime]) -> Optional[datetime]:
        if dt is not None and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @classmethod
    def _to_domain(cls, model: IncidentModel) -> Incident:
        timeline = [
            TimelineEntry(
                id=t.id,
                incident_id=t.incident_id,
                timestamp=cls._ensure_tz(t.timestamp) or datetime.now(timezone.utc),
                content=t.content,
                source_channel=t.source_channel,
                importance_score=t.importance_score,
                is_major_event=t.is_major_event,
                message_id=t.message_id,
            )
            for t in (model.timeline or [])
        ]
        entities = [
            NamedEntity(
                name=e.name,
                entity_type=EntityType(e.entity_type) if e.entity_type in EntityType._value2member_map_ else EntityType.OTHER,
                normalized_name=e.normalized_name,
                relevance_score=e.relevance_score,
            )
            for e in (model.entities or [])
        ]
        claims = [
            Claim(
                id=c.id,
                incident_id=c.incident_id,
                message_id=c.message_id,
                statement=c.statement,
                source_name=c.source_name,
                confidence=c.confidence,
                is_disputed=c.is_disputed,
                extracted_at=cls._ensure_tz(c.extracted_at),
            )
            for c in (model.claims or [])
        ]

        return Incident(
            id=model.id,
            title=model.title,
            category=model.category,
            status=IncidentStatus(model.status),
            severity=IncidentSeverity(model.severity),
            importance_score=model.importance_score,
            confidence_score=model.confidence_score,
            summary=model.summary or "",
            why_it_matters=model.why_it_matters or "",
            sources=model.sources_list,
            entities=entities,
            timeline=timeline,
            claims=claims,
            contradictions_count=model.contradictions_count,
            created_at=cls._ensure_tz(model.created_at),
            updated_at=cls._ensure_tz(model.updated_at),
            resolved_at=cls._ensure_tz(model.resolved_at),
        )

    async def get(self, incident_id: int) -> Optional[Incident]:
        async with self._session_factory() as session:
            stmt = (
                select(IncidentModel)
                .where(IncidentModel.id == incident_id)
                .options(*self._eager_options())
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_domain(model) if model else None

    async def create(self, incident: Incident) -> Incident:
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            async with session.begin():
                model = IncidentModel(
                    title=incident.title,
                    category=incident.category,
                    status=incident.status.value,
                    severity=incident.severity.value,
                    importance_score=incident.importance_score,
                    confidence_score=incident.confidence_score,
                    summary=incident.summary,
                    why_it_matters=incident.why_it_matters,
                    sources_json=json.dumps(list(set(incident.sources))),
                    contradictions_count=incident.contradictions_count,
                    created_at=incident.created_at or now,
                    updated_at=incident.updated_at or now,
                    resolved_at=incident.resolved_at,
                )
                session.add(model)
                await session.flush()
                incident.id = model.id

                # Persist timeline
                for t in incident.timeline:
                    tm = TimelineModel(
                        incident_id=model.id,
                        timestamp=t.timestamp,
                        content=t.content,
                        source_channel=t.source_channel,
                        importance_score=t.importance_score,
                        is_major_event=t.is_major_event,
                        message_id=t.message_id,
                    )
                    session.add(tm)

                # Persist entities
                for ent in incident.entities:
                    em = EntityModel(
                        incident_id=model.id,
                        name=ent.name,
                        entity_type=ent.entity_type.value,
                        normalized_name=ent.normalized_name,
                        relevance_score=ent.relevance_score,
                    )
                    session.add(em)

                # Persist claims
                for cl in incident.claims:
                    cm = ClaimModel(
                        incident_id=model.id,
                        message_id=cl.message_id,
                        statement=cl.statement,
                        source_name=cl.source_name,
                        confidence=cl.confidence,
                        is_disputed=cl.is_disputed,
                        extracted_at=cl.extracted_at or now,
                    )
                    session.add(cm)

                await session.flush()
                return incident

    async def update(self, incident: Incident) -> Incident:
        if incident.id is None:
            raise ValueError("Cannot update incident without an ID")

        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            async with session.begin():
                stmt = (
                    update(IncidentModel)
                    .where(IncidentModel.id == incident.id)
                    .values(
                        title=incident.title,
                        category=incident.category,
                        status=incident.status.value,
                        severity=incident.severity.value,
                        importance_score=incident.importance_score,
                        confidence_score=incident.confidence_score,
                        summary=incident.summary,
                        why_it_matters=incident.why_it_matters,
                        sources_json=json.dumps(list(set(incident.sources))),
                        contradictions_count=incident.contradictions_count,
                        updated_at=now,
                        resolved_at=incident.resolved_at,
                    )
                )
                await session.execute(stmt)
                incident.updated_at = now
                return incident

    async def find_candidates(self, message: Message) -> List[Incident]:
        active_statuses = [
            IncidentStatus.NEW.value,
            IncidentStatus.DEVELOPING.value,
            IncidentStatus.MONITORING.value,
        ]
        async with self._session_factory() as session:
            stmt = (
                select(IncidentModel)
                .where(IncidentModel.status.in_(active_statuses))
                .options(*self._eager_options())
            )
            if message.category and message.category != "uncategorized":
                stmt = stmt.where(
                    or_(
                        IncidentModel.category == message.category,
                        IncidentModel.importance_score >= 7.0,
                    )
                )
            stmt = stmt.order_by(IncidentModel.updated_at.desc()).limit(15)
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def list_active(self) -> List[Incident]:
        active_statuses = [
            IncidentStatus.NEW.value,
            IncidentStatus.DEVELOPING.value,
            IncidentStatus.MONITORING.value,
        ]
        async with self._session_factory() as session:
            stmt = (
                select(IncidentModel)
                .where(IncidentModel.status.in_(active_statuses))
                .options(*self._eager_options())
                .order_by(IncidentModel.importance_score.desc())
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def list_by_status(self, status: IncidentStatus) -> List[Incident]:
        async with self._session_factory() as session:
            stmt = (
                select(IncidentModel)
                .where(IncidentModel.status == status.value)
                .options(*self._eager_options())
                .order_by(IncidentModel.importance_score.desc())
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> List[Incident]:
        async with self._session_factory() as session:
            stmt = select(IncidentModel).options(*self._eager_options())
            conditions = []
            if query:
                pattern = f"%{query}%"
                conditions.append(
                    or_(
                        IncidentModel.title.ilike(pattern),
                        IncidentModel.summary.ilike(pattern),
                        IncidentModel.why_it_matters.ilike(pattern),
                    )
                )
            if category:
                conditions.append(IncidentModel.category == category)

            if conditions:
                stmt = stmt.where(*conditions)

            stmt = stmt.order_by(IncidentModel.updated_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def add_timeline_entry(self, entry: TimelineEntry) -> TimelineEntry:
        async with self._session_factory() as session:
            async with session.begin():
                model = TimelineModel(
                    incident_id=entry.incident_id,
                    timestamp=entry.timestamp,
                    content=entry.content,
                    source_channel=entry.source_channel,
                    importance_score=entry.importance_score,
                    is_major_event=entry.is_major_event,
                    message_id=entry.message_id,
                )
                session.add(model)
                await session.flush()
                entry.id = model.id
                return entry

    async def add_claim(self, claim: Claim) -> Claim:
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            async with session.begin():
                model = ClaimModel(
                    incident_id=claim.incident_id,
                    message_id=claim.message_id,
                    statement=claim.statement,
                    source_name=claim.source_name,
                    confidence=claim.confidence,
                    is_disputed=claim.is_disputed,
                    extracted_at=claim.extracted_at or now,
                )
                session.add(model)
                await session.flush()
                claim.id = model.id
                return claim
