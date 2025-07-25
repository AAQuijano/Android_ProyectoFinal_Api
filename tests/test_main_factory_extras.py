import pytest
from httpx import AsyncClient, ASGITransport
from app.main_factory import create_app


@pytest.mark.asyncio
async def test_root_path_returns_ok():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "API" in response.text or "ok" in response.text.lower()


@pytest.mark.asyncio
async def test_docs_route_exists():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/docs")
        assert response.status_code == 200
        assert "Swagger" in response.text or "FastAPI" in response.text


@pytest.mark.asyncio
async def test_openapi_route_exists():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        assert "paths" in response.text
