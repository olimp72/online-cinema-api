import os
import secrets
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.api.auth import router as auth_router
from app.api.movies import router as movies_router
from app.api.cart import router as cart_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router

security = HTTPBasic()


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    expected_user = os.getenv("SWAGGER_USER", "admin")
    expected_password = os.getenv("SWAGGER_PASSWORD", "admin")

    correct_username = secrets.compare_digest(credentials.username, expected_user)
    correct_password = secrets.compare_digest(credentials.password, expected_password)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password for Swagger",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


app = FastAPI(title="Online Cinema API", version="1.0.0", docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/docs", include_in_schema=False)
async def get_documentation(username: str = Depends(get_current_username)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Documentation")


@app.get("/openapi.json", include_in_schema=False)
async def openapi(username: str = Depends(get_current_username)):
    return app.openapi()


app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(movies_router, prefix="/movies", tags=["Movies"])
app.include_router(cart_router, prefix="/cart", tags=["Cart"])
app.include_router(orders_router, prefix="/orders", tags=["Orders"])
app.include_router(payments_router, prefix="/payments", tags=["Payments"])
