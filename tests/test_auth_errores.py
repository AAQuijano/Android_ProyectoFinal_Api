
import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import Session
from app.main_factory import create_app
from app import models
from app.db import engine
from app.auth import create_access_token

@pytest.fixture
def test_app():
    return create_app()

@pytest.fixture(scope="function", autouse=True)
def setup_db():
    models.SQLModel.metadata.create_all(engine)
    yield
    models.SQLModel.metadata.drop_all(engine)

@pytest.fixture
def test_user():
    with Session(engine) as session:
        user = models.User(
            name_complete="Test User",
            name_user="test_user",
            cedula="12121212",
            email="test@user.com",
            gender="male",
            role="student",
            hashed_password=models.pwd_context.hash("secret123")
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

@pytest.mark.asyncio
async def test_login_invalid_password(test_app, test_user):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/token",
            data={
                "username": test_user.name_user,
                "password": "wrongpassword",
                "grant_type": "password"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 401
        assert "Credenciales inválidas" in response.text

@pytest.mark.asyncio
async def test_login_nonexistent_user(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/token",
            data={
                "username": "unknown_user",
                "password": "doesntmatter",
                "grant_type": "password"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_access_with_invalid_token(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/usuarios/",
            headers={"Authorization": "Bearer this.is.not.valid"}
        )
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_access_without_token(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/usuarios/")
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_health_is_open(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
