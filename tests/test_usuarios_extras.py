import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_estudiante_no_lista_usuarios(test_app, student_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/usuarios/", headers={"Authorization": f"Bearer {student_token}"})
        assert r.status_code == 403


@pytest.mark.asyncio
async def test_estudiante_no_actualiza_otro_usuario(test_app, student_token, test_admin):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        update = {
            "name_complete": "Hackeado"
        }
        r = await client.patch(f"/usuarios/{test_admin.user_id}", json=update, headers={"Authorization": f"Bearer {student_token}"})
        assert r.status_code == 403


@pytest.mark.asyncio
async def test_historial_estudiante_no_existente(test_app, professor_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/usuarios/9999/historial", headers={"Authorization": f"Bearer {professor_token}"})
        assert r.status_code == 404
