import pytest
from httpx import AsyncClient
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User


async def override_get_current_user():
    return User(id=1, email="testcart@example.com", is_active=True)


@pytest.mark.asyncio
async def test_get_cart(async_client: AsyncClient):
    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await async_client.get("/cart/")

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 1
    assert "items" in data
    assert isinstance(data["items"], list)

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_add_to_cart_invalid_movie(async_client: AsyncClient):
    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await async_client.post("/cart/items", json={"movie_id": 9999})

    assert response.status_code in [400, 404]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_remove_from_cart_not_found(async_client: AsyncClient):
    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await async_client.delete("/cart/items/9999")

    assert response.status_code in [404, 400]

    app.dependency_overrides.clear()
