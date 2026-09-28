"""
Database connection, session management, and engine initialization.
Supports PostgreSQL (asyncpg) and SQLite (aiosqlite).
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all persistent models."""
    pass


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine(database_url: str | None = None) -> AsyncEngine:
    """Retrieve or create async SQLAlchemy engine."""
    global _engine
    if _engine is None or database_url is not None:
        url = database_url or get_settings().database_url
        # If standard postgres:// or sqlite:/// provided without async driver, adapt appropriately
        if url.startswith("sqlite:///"):
            url = url.replace("sqlite:///", "sqlite+aiosqlite:///")
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://")

        _engine = create_async_engine(
            url,
            echo=False,
            future=True,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory(engine: AsyncEngine | None = None) -> async_sessionmaker[AsyncSession]:
    """Retrieve or create async session factory."""
    global _sessionmaker
    if _sessionmaker is None or engine is not None:
        eng = engine or get_engine()
        _sessionmaker = async_sessionmaker(
            bind=eng,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _sessionmaker


async def init_db(database_url: str | None = None) -> None:
    """Create all database tables based on registered models."""
    # Ensure models are imported before metadata creation
    from app.storage import models  # noqa: F401

    engine = get_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose of engine connections."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None
