import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Dynamic test configuration using database targets 
# For true isolation, a separate 'ap_automation_test_db' is recommended in production
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:SecurePass2026@localhost:5433/ap_automation_db"

@pytest.fixture(scope="session")
def test_engine_url():
    """Provides the database URL to build per-session engines."""
    return TEST_DATABASE_URL

@pytest.fixture
async def db_session(test_engine_url) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a transactional wrapper per test case. 
    Creates a fresh engine and session per test to avoid event loop conflicts.
    Always rolls back changes automatically to keep tests decoupled and idempotent.
    """
    engine = create_async_engine(test_engine_url, echo=False)
    async_session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    async with async_session_factory() as session:
        # Start a local transaction block
        await session.begin()
        yield session
        # Explicitly roll back modifications to retain database state integrity
        await session.rollback()
    
    await engine.dispose()