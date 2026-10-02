import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=DEBUG,
    connect_args={"statement_cache_size": 0}
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
