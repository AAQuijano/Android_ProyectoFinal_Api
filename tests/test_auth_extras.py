
import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.config import Settings
from app.auth.auth import create_access_token

settings = Settings()

@pytest.mark.asyncio
async def test_token_expirado(test_app):
    expired_token = jwt.encode(
        {"sub": "expired_user", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/usuarios/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert r.status_code == 401
        assert "credenciales" in r.text

@pytest.mark.asyncio
async def test_usuario_no_encontrado(test_app, db):
    token = create_access_token({"sub": "usuario_inexistente", "user_id": 9999, "role": "student"})
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/usuarios/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401
        assert "credenciales" in r.text

@pytest.mark.asyncio
async def test_rol_no_permitido(test_app, db, student_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/materias/", json={
            "materia": "Test Privado",
            "description": "No autorizado",
            "professor_id": 1
        }, headers={"Authorization": f"Bearer {student_token}"})
        assert r.status_code == 403

@pytest.mark.asyncio
async def test_token_mal_formado(test_app):
    bad_token = "malformado.token.abc"
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/usuarios/me", headers={"Authorization": f"Bearer {bad_token}"})
        assert r.status_code == 401
