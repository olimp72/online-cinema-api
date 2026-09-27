from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.db.database import engine, Base

app = FastAPI(title="Online Cinema API", version="1.0.0")

@app.on_event("startup")
async def startup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
