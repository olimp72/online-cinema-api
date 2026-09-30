import pytest
from httpx import AsyncClient
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User


async def override_get_current_user():
    return User(id=1, email="testorder@example.com", is_active=True, group_id=1)


@pytest.mark.asyncio
async def test_create_order_empty_cart(async_client: AsyncClient):
    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await async_client.post("/orders/")

    assert response.status_code == 400
    assert response.json()["detail"] == "Cart is empty"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_orders(async_client: AsyncClient):
    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await async_client.get("/orders/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

    app.dependency_overrides.clear()
