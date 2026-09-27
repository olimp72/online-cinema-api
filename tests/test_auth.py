import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient):
    response = await async_client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "StrongPassword123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_login_user_not_active(async_client: AsyncClient):
    await async_client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "StrongPassword123!"}
    )
    response = await async_client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "StrongPassword123!"}
    )
    assert response.status_code == 403
