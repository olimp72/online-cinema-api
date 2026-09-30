import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_movies_empty(async_client: AsyncClient):
    response = await async_client.get("/movies/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_movies_pagination_and_search(async_client: AsyncClient):
    response = await async_client.get("/movies/?skip=0&limit=5&search=Matrix")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_movies_filter_by_year_and_imdb(async_client: AsyncClient):
    response = await async_client.get("/movies/?year=2023&min_imdb=8.0")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
