import asyncio
from datetime import datetime
from sqlalchemy import delete
from app.core.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.models.user import ActivationToken

async def _delete_expired_tokens():
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(ActivationToken).where(ActivationToken.expires_at < datetime.utcnow())
        )
        await session.commit()

@celery_app.task
def delete_expired_tokens():
    asyncio.run(_delete_expired_tokens())
