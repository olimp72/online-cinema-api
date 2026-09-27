from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api.movies import router as movies_router
from app.api.cart import router as cart_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.db.database import engine, Base

app = FastAPI(title="Online Cinema API", version="1.0.0")

@app.on_event("startup")
async def startup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(movies_router, prefix="/movies", tags=["Movies"])
app.include_router(cart_router, prefix="/cart", tags=["Cart"])
app.include_router(orders_router, prefix="/orders", tags=["Orders"])
app.include_router(payments_router, prefix="/payments", tags=["Payments"])
