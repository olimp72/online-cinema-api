import os
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from app.main import app
from app.db.database import get_db, Base

TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5433/cinema_db"
)

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool
)
TestingSessionLocal = sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        await conn.execute(text(
            "INSERT INTO user_groups (id, name) VALUES (1, 'USER'), (2, 'MODERATOR'), (3, 'ADMIN');"
        ))
        await conn.execute(text(
            "SELECT setval(pg_get_serial_sequence('user_groups', 'id'), (SELECT MAX(id) FROM user_groups));"
        ))

        await conn.execute(text(
            "INSERT INTO users (id, email, hashed_password, is_active) "
            "VALUES (1, 'mock_user@example.com', 'fake_password', true);"
        ))
        await conn.execute(text(
            "SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT MAX(id) FROM users));"
        ))

    yield

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
