import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import Session
from app import models
from app.db import engine


@pytest.mark.asyncio
async def test_profesor_no_puede_registrar_para_otros(test_app, professor_token, test_professor):
    otro_profesor_id = test_professor.user_id + 1000  # ID ficticio
    data = {
        "materia": "Matemática Avanzada",
        "description": "Intento ilegal",
        "professor_id": otro_profesor_id
    }
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/materias/", json=data, headers={"Authorization": f"Bearer {professor_token}"})
        assert r.status_code == 403


@pytest.mark.asyncio
async def test_estudiante_no_accede_materias(test_app, student_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/materias/", json={
            "materia": "Historia",
            "description": "Curso",
            "professor_id": 1
        }, headers={"Authorization": f"Bearer {student_token}"})
        assert r.status_code == 403


@pytest.mark.asyncio
async def test_eliminar_materia_inexistente(test_app, professor_token):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.delete("/materias/9999", headers={"Authorization": f"Bearer {professor_token}"})
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_editar_materia_ajena(test_app, db, test_professor, professor_token):
    otro_profesor = models.User(
        name_complete="Otro Profesor",
        name_user="otro_profe",
        cedula="88888888",
        email="otro@profe.com",
        gender="male",
        role="professor",
        hashed_password="hashed"
    )
    db.add(otro_profesor)
    db.commit()
    db.refresh(otro_profesor)

    score = models.Score(materia="Química", professor_id=otro_profesor.user_id)
    db.add(score)
    db.commit()
    db.refresh(score)

    update = {
        "materia": "Actualizada",
        "description": "Edición ilegal",
        "professor_id": test_professor.user_id
    }

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.patch(f"/materias/{score.score_id}", json=update, headers={"Authorization": f"Bearer {professor_token}"})
        assert r.status_code == 403
