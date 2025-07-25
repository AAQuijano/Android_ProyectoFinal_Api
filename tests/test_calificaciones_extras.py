
import pytest
from datetime import date
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_update_calificacion_no_existente(test_app, professor_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        update = {
            "valor": 95,
            "tipo": "parcial",
            "fecha": str(date.today()),
            "comentario": "Actualización inválida",
            "student_id": 999,
            "score_id": 999
        }
        r = await client.patch("/calificaciones/9999", json=update, headers={"Authorization": f"Bearer {professor_token}"})
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_eliminar_calificacion_inexistente(test_app, professor_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.delete("/calificaciones/9999", headers={"Authorization": f"Bearer {professor_token}"})
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_listado_calificaciones_vacio(test_app, db):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/calificaciones/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_calificaciones_por_materia_inexistente(test_app, db):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/calificaciones/por_materia/9999")
        assert r.status_code == 200
        assert r.json() == []
