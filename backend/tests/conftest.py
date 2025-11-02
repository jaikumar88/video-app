"""
Test configuration and fixtures for the WorldClass Video Platform
"""

import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"

from app.core.config import get_settings
from app.core.database import get_db, Base
from app.models.user import User
from app.models.meeting import Meeting, Participant
from main import app


# Test settings
@pytest.fixture(scope="session")
def settings():
    """Get test settings configuration."""
    return get_settings()


# Database fixtures
@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    """Create test database session."""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
def override_get_db(db_session):
    """Override database dependency for testing."""
    async def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


# HTTP Client fixtures
@pytest.fixture(scope="function")
def client(override_get_db):
    """Create test HTTP client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture(scope="function")
async def async_client(override_get_db):
    """Create async test HTTP client."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac


# Authentication fixtures
@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user."""
    from app.services.auth_service import AuthService
    
    auth_service = AuthService(db_session)
    user_data = {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+1234567890"
    }
    
    user = await auth_service.create_user(**user_data)
    user.email_verified = True
    user.phone_verified = True
    user.is_verified = True
    
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def test_user_2(db_session):
    """Create a second test user for multi-user tests."""
    from app.services.auth_service import AuthService
    
    auth_service = AuthService(db_session)
    user_data = {
        "email": "test2@example.com",
        "password": "TestPassword123!",
        "first_name": "Test2",
        "last_name": "User2",
        "phone_number": "+1234567891"
    }
    
    user = await auth_service.create_user(**user_data)
    user.email_verified = True
    user.phone_verified = True
    user.is_verified = True
    
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def authenticated_user(test_user, db_session):
    """Create authenticated user with valid JWT token."""
    from app.services.auth_service import AuthService
    
    auth_service = AuthService(db_session)
    tokens = await auth_service.create_access_token(test_user)
    
    return {
        "user": test_user,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "headers": {"Authorization": f"Bearer {tokens['access_token']}"}
    }


@pytest_asyncio.fixture
async def authenticated_user_2(test_user_2, db_session):
    """Create second authenticated user with valid JWT token."""
    from app.services.auth_service import AuthService
    
    auth_service = AuthService(db_session)
    tokens = await auth_service.create_access_token(test_user_2)
    
    return {
        "user": test_user_2,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "headers": {"Authorization": f"Bearer {tokens['access_token']}"}
    }


# Meeting fixtures
@pytest_asyncio.fixture
async def test_meeting(db_session, test_user):
    """Create a test meeting."""
    meeting = Meeting(
        title="Test Meeting",
        description="Test meeting description",
        host_id=test_user.id,
        max_participants=100,
        status="scheduled"
    )
    
    db_session.add(meeting)
    await db_session.commit()
    await db_session.refresh(meeting)
    
    return meeting


@pytest_asyncio.fixture
async def active_meeting(db_session, test_user):
    """Create an active test meeting."""
    meeting = Meeting(
        title="Active Test Meeting",
        description="Active test meeting description",
        host_id=test_user.id,
        max_participants=100,
        status="active"
    )
    
    db_session.add(meeting)
    await db_session.commit()
    await db_session.refresh(meeting)
    
    return meeting


# Mock services
@pytest.fixture
def mock_email_service(mocker):
    """Mock email service for testing."""
    return mocker.patch("app.services.email_service.EmailService")


@pytest.fixture
def mock_sms_service(mocker):
    """Mock SMS service for testing."""
    return mocker.patch("app.services.sms_service.SMSService")


# WebSocket fixtures
@pytest_asyncio.fixture
async def websocket_client():
    """Create WebSocket test client."""
    from fastapi.testclient import TestClient
    
    with TestClient(app) as client:
        yield client


# Performance testing fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# Test data generators
@pytest.fixture
def user_factory():
    """Factory for generating test user data."""
    from faker import Faker
    fake = Faker()
    
    def _create_user_data(**kwargs):
        data = {
            "email": fake.email(),
            "password": "TestPassword123!",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "phone_number": fake.phone_number()
        }
        data.update(kwargs)
        return data
    
    return _create_user_data


@pytest.fixture
def meeting_factory():
    """Factory for generating test meeting data."""
    from faker import Faker
    fake = Faker()
    
    def _create_meeting_data(**kwargs):
        data = {
            "title": fake.sentence(nb_words=4),
            "description": fake.text(max_nb_chars=200),
            "max_participants": fake.random_int(min=2, max=100),
            "duration_minutes": fake.random_int(min=15, max=120)
        }
        data.update(kwargs)
        return data
    
    return _create_meeting_data


# Utility fixtures
@pytest.fixture
def temp_file():
    """Create temporary file for testing file uploads."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test file content")
        tmp.flush()
        yield tmp.name
    
    # Cleanup
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


@pytest.fixture(autouse=True)
def isolate_db():
    """Ensure database isolation between tests."""
    # This fixture runs automatically before each test
    # Additional isolation logic can be added here if needed
    pass