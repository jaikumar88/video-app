"""
Database configuration and connection management.
Supports both SQLite (local) and PostgreSQL (production).
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Database metadata
metadata = MetaData()


class Base(DeclarativeBase):
    """Base class for all database models."""

    metadata = metadata


# Global variables
engine = None
AsyncSessionLocal = None


def get_database_url() -> str:
    """Get database URL based on environment."""
    settings = get_settings()
    return settings.DATABASE_URL


def create_engine():
    """Create database engine based on environment."""
    global engine

    database_url = get_database_url()
    settings = get_settings()

    if settings.is_local and database_url.startswith("sqlite"):
        # SQLite configuration for local development
        engine = create_async_engine(
            database_url,
            echo=settings.DEBUG,
            connect_args={"check_same_thread": False},
        )
    else:
        # PostgreSQL configuration for production
        engine = create_async_engine(
            database_url,
            echo=settings.DEBUG,
            pool_size=20,
            max_overflow=0,
            pool_pre_ping=True,
            pool_recycle=300,
        )

    return engine


def get_session_factory():
    """Get session factory."""
    global AsyncSessionLocal

    if engine is None:
        create_engine()

    AsyncSessionLocal = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    return AsyncSessionLocal


def initialize_database():
    """Initialize database engine and session factory."""
    create_engine()
    get_session_factory()
    logger.info("Database engine and session factory initialized")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    if AsyncSessionLocal is None:
        get_session_factory()

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db_session() -> AsyncSession:
    """Get database session for direct use (not as dependency)."""
    if AsyncSessionLocal is None:
        get_session_factory()
    
    return AsyncSessionLocal()


async def create_tables():
    """Create all database tables."""
    global engine

    if engine is None:
        initialize_database()

    # Import all models to ensure they are registered
    # These imports are needed for table creation
    from app.models.user import User  # noqa: F401
    from app.models.meeting import Meeting, MeetingParticipant  # noqa: F401
    from app.models.message import Message  # noqa: F401

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def drop_tables():
    """Drop all database tables (for testing)."""
    global engine

    if engine is None:
        initialize_database()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")


# Initialize database connection
def init_db():
    """Initialize database connection."""
    create_engine()
    get_session_factory()
    logger.info("Database connection initialized")
