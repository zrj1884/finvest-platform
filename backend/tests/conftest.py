"""Shared test fixtures."""

import os

# Set TESTING before any app imports
os.environ["TESTING"] = "true"

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://finvest:finvest@localhost:5432/finvest_test")

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestSessionFactory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def client():
    """HTTP test client with DB dependency overridden."""
    from app.db.session import get_db
    from app.main import app

    async def _get_test_db():
        async with TestSessionFactory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

    # Cleanup after test
    async with test_engine.begin() as conn:
        await conn.execute(text("DELETE FROM orders"))
        await conn.execute(text("DELETE FROM positions"))
        await conn.execute(text("DELETE FROM accounts"))
        await conn.execute(text("DELETE FROM users"))
