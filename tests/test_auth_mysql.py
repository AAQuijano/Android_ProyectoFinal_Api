import pytest
from httpx import AsyncClient, ASGITransport
from app.main_factory import create_app
from app.db import get_db
from app.config import settings
from sqlalchemy import create_engine
from sqlmodel import SQLModel

# Usa el engine real desde .env
engine = create_engine(settings.DATABASE_URL, echo=True)

@pytest.fixture(scope="module", autouse=True)
def prepare_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(scope="module")
def test_app():
    app = create_app()
    return app

@pytest.mark.asyncio
async def test_registro_y_login_estudiante(test_app):
    transport = ASGITransport(app=test_app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        estudiante = {
            "name_complete": "Estudiante Uno",
            "name_user": "estudiante1",
            "cedula": "12345670",
            "email": "estu1@example.com",
            "gender": "male",
            "birth_date": "2001-02-15",
            "password": "estupass123",
            "role": "student"
        }

        # Crear usuario
        response = await client.post("/usuarios/", json=estudiante)
        assert response.status_code == 201
        body = response.json()
        assert "student_id" in body
        assert body["name_user"] == "estudiante1"
        assert body["role"] == "student"

        # Login exitoso
        response = await client.post(
            "/token",
            data={
                "username": "estudiante1",
                "password": "estupass123",
                "grant_type": "password"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200
        token = response.json()
        assert "access_token" in token
        assert token["token_type"] == "bearer"
