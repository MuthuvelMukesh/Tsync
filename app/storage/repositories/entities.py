"""
Entity repository protocol and SQLAlchemy implementation.
Manages named entities and links to incidents.
"""

from typing import List, Protocol
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.entities import NamedEntity, EntityType
from app.storage.models import EntityModel


class EntityRepository(Protocol):
    """Abstract interface for named entity storage."""

    async def get_by_incident(self, incident_id: int) -> List[NamedEntity]:
        ...

    async def search(self, name_query: str) -> List[NamedEntity]:
        ...

    async def add_entity_to_incident(
        self, incident_id: int, entity: NamedEntity
    ) -> NamedEntity:
        ...


class SQLAlchemyEntityRepository:
    """SQLAlchemy implementation of EntityRepository."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _to_domain(model: EntityModel) -> NamedEntity:
        etype = EntityType.OTHER
        if model.entity_type in EntityType._value2member_map_:
            etype = EntityType(model.entity_type)
        return NamedEntity(
            name=model.name,
            entity_type=etype,
            normalized_name=model.normalized_name,
            relevance_score=model.relevance_score,
        )

    async def get_by_incident(self, incident_id: int) -> List[NamedEntity]:
        async with self._session_factory() as session:
            stmt = select(EntityModel).where(EntityModel.incident_id == incident_id)
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def search(self, name_query: str) -> List[NamedEntity]:
        clean = name_query.strip().lower()
        async with self._session_factory() as session:
            stmt = (
                select(EntityModel)
                .where(EntityModel.normalized_name.contains(clean))
                .limit(30)
            )
            result = await session.execute(stmt)
            return [self._to_domain(m) for m in result.scalars().all()]

    async def add_entity_to_incident(
        self, incident_id: int, entity: NamedEntity
    ) -> NamedEntity:
        async with self._session_factory() as session:
            async with session.begin():
                model = EntityModel(
                    incident_id=incident_id,
                    name=entity.name,
                    entity_type=entity.entity_type.value,
                    normalized_name=entity.normalized_name,
                    relevance_score=entity.relevance_score,
                )
                session.add(model)
                await session.flush()
                return self._to_domain(model)
